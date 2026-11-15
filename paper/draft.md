# Do LLMs mirror how you ask? DISC-styled questions and the answers they get

Draft, v1: background and method. Results and discussion come after the experiment runs.

## Introduction

People write to chatbots in different voices. Some open with the bottom line and want the same
back. Some add a line about why they are asking and how much they look forward to the result.
Some apologise for the trouble and say there is no rush, and some spell out every condition and
ask for exactness. The question underneath can be the same in all four cases. This study asks
whether that difference in voice reaches the answer, and whether it makes the answer better or
worse.

Much prompt research changes what the model is told to be. Persona and role prompts put a
description of the model ("you are an expert mathematician") in the system prompt or before the
question, and a line of work measures whether that helps (Zheng et al., 2023; Salewski et al.,
2023; Kong et al., 2023). This study changes the other side of the conversation. The model is
never told to adopt a style, and there is no system prompt at all. Only the asker's voice
changes, and everything the question asks for stays fixed.

To vary the voice in a controlled way, the study borrows the four DISC labels: D (Dominance), i
(Influence), S (Steadiness) and C (Conscientiousness). DISC is a commercial profiling model,
and its standing as psychology is weak (see "Limits of DISC" below). It is used here for a
narrower reason. Each label names a voice that most readers recognise: brief and outcome-first
for D, warm and enthusiastic for i, calm and patient for S, precise and careful for C. That
gives four distinct and nameable ways to ask the same question. The study makes no claim that
these voices map to personality types, or that any user "is" a D or a C.

Two questions follow. First, does the model mirror the voice, so that a D question gets a
shorter, more directive reply and an i question a warmer one? Second, does the voice change how
good the answer is: whether a maths answer is right, how far apart a list of unrelated words
lands, how a blind judge rates an email or a piece of advice, and whether an SVG drawing meets
its brief? The second question matters for anyone who writes prompts, because every question a
user writes comes in some voice.

This draft covers the background, the hypotheses and the method as built. The task set, runner
and graders are in this repository, and the experiment has not been run yet.

## Related work

### Persona prompting

Zheng et al. (2023) tested 162 personas in system prompts on 4 families of models and 2,410
factual questions, and found that adding a persona did not improve performance. They also found
that the effect of a given persona can be largely random, and that automatically picking the
best persona for a question is hard. Salewski et al. (2023) asked models to impersonate people
of different ages, expertise and social identity. Models impersonating domain experts did
better than models impersonating non-experts, and impersonation also exposed biases: a model
prompted as a man described cars better than one prompted as a woman. Kong et al. (2023)
reported that role-play prompting generally beat standard zero-shot prompting on twelve
reasoning benchmarks; accuracy on AQuA, for example, rose from 53.5% to 63.8%.

These studies change the model's assigned identity. The present study holds the model's
identity fixed (it has none beyond its defaults) and changes the user's voice. The persona
results still set an expectation: wording around a question can move accuracy, but the
direction is hard to predict and often small.

### Tone, politeness and emotional framing

Closer to this study is work that changes the tone of the request itself. Yin et al. (2024)
varied politeness in English, Chinese and Japanese prompts. Impolite prompts often led to poor
performance, overly polite language did not guarantee better results, and the best politeness
level differed by language. Dobariya and Kumar (2025) rewrote 50 multiple-choice questions into
five tones from Very Polite to Very Rude and tested them on ChatGPT-4o. In their data the rude
prompts did better, with accuracy from 80.8% for Very Polite to 84.8% for Very Rude, which runs
against the earlier result and suggests newer models may respond to tone differently. Li et al.
(2023) added emotional phrases to prompts ("EmotionPrompt") and reported better performance
across 45 tasks and several models, along with gains on generative tasks in a human study with
106 participants.

Two points from this work shape the design here. First, the results disagree across models and
years, so a study should test more than one model family and keep the full records. Second,
these studies mostly score accuracy on questions with one right answer. Tone could also change
open-ended answers, creative output and generated code, and those need other measures.

Small, meaning-preserving changes to a prompt can move results a lot. Sclar et al. (2023) found
accuracy differences of up to 76 points from formatting changes alone in few-shot prompts on
LLaMA-2-13B, and the sensitivity did not go away with larger models, more examples or
instruction tuning. That is a warning for this study: a style rewrite also changes wording and
length, so any effect found belongs to the rewrites as written. The design limits this by
keeping facts, numbers and the required output format identical across versions (see Method).

### Mirroring and agreement

People in conversation tend to converge on each other's way of talking. Danescu-Niculescu-Mizil
et al. (2011) tested this accommodation effect on a large set of Twitter conversations and
found it held in that setting, with a more complex pattern of influence than earlier small lab
studies had shown. If language models learn from such text, they may mirror a user's style too.

A related behaviour is sycophancy. Sharma et al. (2023) found that five AI assistants
consistently showed sycophancy across four free-form tasks, and that both humans and preference
models sometimes preferred convincing sycophantic answers over correct ones. Sycophancy is
about agreeing with a user's stated views. This study has no stated views in its questions,
only a voice. It measures whether the model takes on the voice (mirroring) separately from
whether the answer gets better or worse.

### Limits of DISC

DISC goes back to William Moulton Marston's 1928 book *Emotions of Normal People*, which has
chapters on dominance, compliance, submission and inducement as emotions (Marston, 1928).
Marston wrote a theory of emotions; the DISC profiles used at work today are commercial
questionnaires. Everything DiSC, one of them, describes D as "active and questioning", i as
"active and accepting", S as "thoughtful and accepting" and C as "thoughtful and questioning",
and characterises each style by its behaviour and priorities: D people prioritise getting
results, i people enjoy collaboration, S people are patient and want a predictable environment,
and C people focus on accuracy (Everything DiSC, n.d.).

Independent evidence for DISC as a measure of personality is thin. Martinussen et al. (2001)
gave 103 undergraduates both the ipsative (forced-choice) and the normative version of a
DISC-type test, DISCUS, together with a Big Five questionnaire. The two versions were not
equivalent, and the four DISC dimensions turned out to be combinations of Big Five traits
rather than independent traits.

This study takes no position on whether DISC describes people. It uses the four labels only as
a vocabulary for four voices that can be written down and checked. Whether the rewrites read as
the intended voices is checked directly with a style classifier (see Method).

### Measures this study builds on

The creativity area uses the Divergent Association Task (DAT) of Olson et al. (2021).
Participants name 10 words that are as different from each other as possible. The score is the
mean cosine distance between GloVe embeddings over all 21 pairs of the first seven valid words,
times 100; the three extra words are a buffer for typos and words the model lacks. Olson et al.
collected the task from 8,914 participants, and higher scores correlated with two established
creativity measures. Chen and Ding (2023) applied the DAT to language models and found that
GPT-4 with greedy decoding outscored 96% of humans, and that sampling and higher temperature
raised scores for other models at the cost of stability. The embeddings are GloVe (Pennington
et al., 2014) trained on Common Crawl, in the `glove.840B.300d` release that the reference DAT
code uses (Olson, n.d.).

The generation area scores rendered images against their brief with CLIP, a model trained on
400 million image-text pairs to predict which caption goes with which image (Radford et al.,
2021). Hessel et al. (2021) showed that CLIP similarity works as a reference-free metric for
image captions, with high correlation with human judgements on several corpora. This study uses
the OpenAI ViT-B-32 weights through OpenCLIP, whose documentation notes that the OpenAI weights
use the QuickGELU activation (Ilharco et al., 2021).

Open-ended answers are scored by language-model judges. Zheng et al. (2023b) found that strong
judges agree with human preferences over 80% of the time, about as often as humans agree with
each other, and named position, verbosity and self-enhancement biases. Wang et al. (2023)
showed that the ranking of two answers can flip just by changing the order they appear in, and
proposed aggregating over both orders. Panickssery et al. (2024) found that judges recognise
and favour their own outputs. The pairwise grader here follows the order-swapping fix and
reports each judge separately (see Method).

Sentiment in the mirroring grader comes from VADER, a lexicon and rule-based sentiment model
built for social media text, whose compound score runs from -1 (most negative) to +1 (most
positive) (Hutto and Gilbert, 2014).

## Hypotheses

The hypotheses are about the question's voice only. The model is never told to adopt a style,
and the rewrites are not exaggerated.

H1 (mirroring). Replies move in the direction of the question's voice, compared with the same
model's reply to the neutral question for the same task and sample. D replies are shorter and
use more directive phrases. i replies have more exclamation marks and more positive sentiment.
S replies use more hedges. C replies are longer.

H2 (accuracy). Style does not change accuracy on correctness tasks by much. On questions with
one right answer, persona and tone effects have been small, random or in opposite directions
across studies (Zheng et al., 2023; Yin et al., 2024; Dobariya and Kumar, 2025). A style that
leads the model to drop the `ANSWER:` line would show up here as lost accuracy.

H3 (creativity). Style changes DAT scores. The direction is open: an enthusiastic i voice may
widen the range of words, and a precise C voice may narrow it.

H4 (open-ended quality). Judged quality of styled answers differs from neutral answers, so the
styled win rate moves away from 0.5. The direction may differ by style; for example, a D voice
that asks for a quick verdict may get thinner advice.

H5 (generation). Style changes SVG output little on the explicit, checkable parts of a brief
(whether it renders, constraints met), and any effect shows first in CLIP similarity, where the
model has more freedom.

Each hypothesis is tested per model, because the tone literature suggests effects differ
between models.

## Method

### Design

Every task is written in five versions: neutral, D, i, S and C. Each version is sent to each
tested model as a single user message containing only the version text. There is no system
prompt and no instruction about style. Each model answers each version three times. Graders
compare each styled answer with the same model's neutral answer to the same task and sample, so
the neutral version is the baseline throughout.

### Task set

The set has 21 tasks in four areas. Each task is one YAML file with an `id` (equal to the file
name), an `area`, a `grader`, a written `rationale` for its inclusion, the five `versions`, and
an `expected` block that holds the answer or constraints when the grader needs them. A loader
validates every file before a run.

| Area | Tasks | Grader | What the tasks are |
|---|---|---|---|
| Correctness | 6 | exact match | A pen-price ratio, a height ordering puzzle, a chemical symbol, a train arrival time, counting a letter in a phrase, the weekday of a leap day |
| Creativity | 3 | DAT | The standard DAT, and the same task framed as a party word game and as seeds for a writing exercise |
| Quality | 6 | pairwise judge | An email to a landlord, a choice between two job offers, explaining vaccines to a 12-year-old, a half-marathon plan, product copy for a water bottle, cutting one of three app features |
| Generation | 6 | SVG | A red ball, a traffic light, an OPEN sign, a house, a bar chart, a smiley face |

The rationales are specific to each task. The pen-price task, for example, is a one-step ratio
with a single integer answer, so any accuracy drop would come from the style alone. The
job-offer task has a pay and commute trade-off, where a voice that wants a quick verdict might
get a thinner justification. The smiley face has the most constraints in the set (a circle
count, a curved path, a colour and a canvas size), to test whether detail survives every voice.

### Style-only rewrites

The rewrites change only the asker's voice. Each one keeps the same facts, the same numbers and
the same request. The D version is brief and outcome-first ("I need a pen count."). The i
version adds warm personal context ("I'm stocking up on pens for our team's craft afternoon and
I'm so excited about it!"). The S version is patient and thankful ("No rush at all, whenever
you have a moment."). The C version stresses exactness ("To be exact: the shop's listed price
is 3 pens for $2...").

Two checks hold the rewrites to that rule. A script (`check_style_only`) confirms that every
styled version contains the same multiset of numbers as neutral, and that for correctness, DAT
and SVG tasks its last line is identical to neutral's. That last line is the fixed format
instruction, such as `End your reply with a last line in the form ANSWER: <integer>` or `Reply
with exactly 10 nouns, one per line, and nothing else.` For correctness tasks the line must
contain `ANSWER:`. The current task set passes with no problems.

The second check asks whether the styles are recognisable at all. A style classifier
(`disc-classify`) shows a judge model each question text in a seeded random order, with short
descriptions of the five styles, and asks for one label. The judge never sees the task id or
the intended version. The command reports the share of each version labelled correctly. It
makes live calls, so it is run by hand on the final task set before the experiment.

### Models and sampling

All settings come from `config/models.yaml`.

| Role | Name | Model (LiteLLM id) | max_tokens |
|---|---|---|---|
| Tested | claude | `anthropic/claude-sonnet-4-5` | 1024 |
| Tested | gemini | `gemini/gemini-2.5-flash` | 1024 |
| Tested | open-weights | `openrouter/meta-llama/llama-3.3-70b-instruct` | 1024 |
| Judge | claude-judge | `anthropic/claude-sonnet-4-5` | 512 |
| Judge | gemini-judge | `gemini/gemini-2.5-flash` | 512 |

The tested models cover three families: Anthropic, Google and Meta's open-weights Llama,
reached through OpenRouter. They are sampled at temperature 0.7, three samples per prompt. That
gives 21 tasks × 5 versions × 3 samples = 315 calls per model and 945 in total. Judges and the
style classifier run at temperature 0.

The two judges come from different families. They are the same models as two of the tested
models, so each judge also rates its own family's answers. Because judges can favour their own
outputs (Panickssery et al., 2024), the pairwise grader reports win rates per judge as well as
pooled, so any self-preference stays visible in the per-judge numbers.

### Runner

The runner (`disc-run`) is a thin loop on LiteLLM. For every task, version, model and sample it
sends one call and appends one JSONL record: task id, version, model name, LiteLLM id, sample
index, temperature, `max_tokens`, the prompt, the raw output, input and output token counts,
and a timestamp. Failed calls are retried up to three times. Rerunning with the same output
file skips calls already recorded, and the runner refuses to continue if a recorded call used a
different model id, temperature, `max_tokens` or prompt, so one file never mixes two setups.

A dry run builds every prompt and estimates the cost without any network call. Input tokens are
counted locally with one tokenizer for all models, output is assumed to reach `max_tokens`, and
prices per million tokens come from the config. Judge calls are estimated the same way, with
the judge's input taken as the neutral question plus two answers at the tested model's
`max_tokens`. For the current config the estimate is $12.68 in total ($4.89 for claude, $0.81
for gemini, $0.13 for open-weights, $6.85 for judges), within the $50 budget. The runner stops
before calling anything when the estimate exceeds the budget.

### Graders

Every grader reads only run records and task files, and each grades only the tasks whose
`grader` field matches it. There is no human grading. Graders that compare against neutral skip
a styled answer whose neutral partner is missing or whose output is empty, and print how many
they skipped.

#### Correctness: exact match

The grader takes the value after `ANSWER:` on the last line that has one and compares it with
the task's expected answer, ignoring case, surrounding space and a trailing period. A reply
with no `ANSWER:` line counts as wrong. With one right answer per task, a string comparison
needs no judge and so adds no judge bias, and counting a missing format line as wrong means a
style that makes the model ramble or skip the format shows up as lost accuracy. The grader
prints accuracy per model and version.

#### Mirroring: text features

For correctness and quality tasks, the mirroring grader computes five features of each reply:
word count, hedges per 100 words, directives per 100 words, the number of exclamation marks,
and mean VADER compound sentiment over sentences. Hedges are phrases such as "maybe",
"perhaps", "might" and "it depends"; directives are phrases such as "must", "should", "make
sure" and "avoid". For each styled reply it subtracts the features of the same model's neutral
reply to the same task and sample, and prints the mean difference per model and style.

The features follow the surface signature of each voice: D short and directive, i exclamations
and warm sentiment, S soft and hedged, C long and careful. Counting them shows which way a
style moved the reply without asking a judge. DAT and SVG replies are left out because their
format is fixed and leaves little room for voice.

#### Creativity: Divergent Association Task

The DAT tasks ask for exactly 10 nouns, one per line. The grader cleans each line (removing
list numbers, bullets and surrounding punctuation, and lowercasing), keeps the unique words
that appear in the GloVe vocabulary, and takes the first seven. The score is the mean cosine
distance over all 21 pairs times 100, following Olson et al. (2021); a higher score means the
words are further apart in meaning. A reply with fewer than seven known words gets no score and
is counted. The GloVe vectors are the first 200,000 lines of the 840B 300-dimensional release,
keeping lowercase alphabetic words only. Embedding distance needs no judge model and carries no
judge bias. The grader prints the mean score per model and version.

#### Open-ended quality: blind pairwise judging

For quality tasks, each styled answer is paired with the neutral answer for the same model,
task and sample. Each judge sees the neutral question and the two answers labelled A and B, and
is asked which answer is better, with a last line `WINNER: <A|B|TIE>`. The judge never sees the
styled question, the style, the task id or the model name, so it picks on quality alone. Every
pair is judged in both orders, as Wang et al. (2023) recommend against position bias. A styled
win counts 1, a tie 0.5 and a loss 0, and verdicts that cannot be parsed are left out of the
rate and counted. The grader prints the styled win rate per model and style, overall and per
judge; 0.5 means no difference from neutral. With 6 tasks, 4 styles, 3 samples, 3 models, 2
orders and 2 judges, a full run makes 864 judge calls.

#### Generation: SVG

An SVG brief can fail in three separate ways, so the grader reports three measures. It takes
the first SVG in the reply (a fenced code block holding `<svg`, or else the first
`<svg>...</svg>` span). Whether the image renders with resvg shows whether the model produced
usable markup. The share of the task's constraints met is a deterministic check of the brief's
explicit demands. The constraint grammar has five forms: `element:<tag>` (at least one such
element), `count:<tag>:<n>` (at least n), `color:<#rrggbb>` (a fill or stroke, as an attribute
or in a `style`), `text:<s>` (a text element containing s) and `viewbox:<w> <h>`. Invalid XML
fails every constraint.

The third measure is CLIP similarity between the rendered image and the brief, as cosine
similarity times 100, a soft check that the picture looks like what was asked. The CLIP text is
the neutral brief without its format line, the same for all five versions, so a styled answer
is never scored against its own wording. CLIP runs only on images that render. The grader
prints, per model and version, the share that renders, the mean share of constraints met and
the mean CLIP similarity.

### Reproducibility

The study needs a fresh clone, `uv sync`, `uv run disc-fetch` and API keys for the three
providers. `disc-fetch` downloads the GloVe vectors and the CLIP weights into `data/`, which is
never committed, and the graders load only these local files. The dry run and the test suite
make no network calls. Each grader is tested on hand-made answers with known scores.

### Scope

Version 1 reports descriptive measures per model, style and task area; it builds no
significance tests. It covers single-turn questions only, uses no human raters, and calls no
image-generation model: the SVG area tests what a language model writes as code.

## References

Chen, H., & Ding, N. (2023). Probing the creativity of large language models: Can models
produce divergent semantic association? Findings of EMNLP 2023.
https://arxiv.org/abs/2310.11158

Danescu-Niculescu-Mizil, C., Gamon, M., & Dumais, S. (2011). Mark my words! Linguistic style
accommodation in social media. arXiv:1105.0673. https://arxiv.org/abs/1105.0673

Dobariya, O., & Kumar, A. (2025). Mind your tone: Investigating how prompt politeness affects
LLM accuracy. arXiv:2510.04950. https://arxiv.org/abs/2510.04950

Everything DiSC. (n.d.). What is DiSC? Retrieved November 2026.
https://www.everythingdisc.com/what-is-disc/

Hessel, J., Holtzman, A., Forbes, M., Le Bras, R., & Choi, Y. (2021). CLIPScore: A
reference-free evaluation metric for image captioning. EMNLP 2021.
https://arxiv.org/abs/2104.08718

Hutto, C. J., & Gilbert, E. (2014). VADER: A parsimonious rule-based model for sentiment
analysis of social media text. ICWSM-14. Code and description:
https://github.com/cjhutto/vaderSentiment

Ilharco, G., et al. (2021). OpenCLIP. Zenodo, doi:10.5281/zenodo.5143773.
https://github.com/mlfoundations/open_clip

Kong, A., Zhao, S., Chen, H., Li, Q., Qin, Y., Sun, R., Zhou, X., Wang, E., & Dong, X. (2023).
Better zero-shot reasoning with role-play prompting. NAACL 2024.
https://arxiv.org/abs/2308.07702

Li, C., Wang, J., Zhang, Y., Zhu, K., Hou, W., Lian, J., Luo, F., Yang, Q., & Xie, X. (2023).
Large language models understand and can be enhanced by emotional stimuli. arXiv:2307.11760.
https://arxiv.org/abs/2307.11760

Marston, W. M. (1928). Emotions of normal people. Kegan Paul, Trench, Trubner and Co.
https://archive.org/details/emotionsofnormal032195mbp

Martinussen, M., Richardsen, A. M., & Vårum, H. W. (2001). Validation of an ipsative
personality measure (DISCUS). Scandinavian Journal of Psychology, 42(5), 411-416.
https://doi.org/10.1111/1467-9450.00253

Olson, J. A. (n.d.). Divergent Association Task, reference scoring code.
https://github.com/jayolson/divergent-association-task

Olson, J. A., Nahas, J., Chmoulevitch, D., Cropper, S. J., & Webb, M. E. (2021). Naming
unrelated words predicts creativity. PNAS, 118(25), e2022340118.
https://europepmc.org/article/PMC/PMC8237676

Panickssery, A., Bowman, S. R., & Feng, S. (2024). LLM evaluators recognize and favor their own
generations. arXiv:2404.13076. https://arxiv.org/abs/2404.13076

Pennington, J., Socher, R., & Manning, C. D. (2014). GloVe: Global vectors for word
representation. EMNLP 2014, 1532-1543. https://aclanthology.org/D14-1162/

Radford, A., et al. (2021). Learning transferable visual models from natural language
supervision. arXiv:2103.00020. https://arxiv.org/abs/2103.00020

Salewski, L., Alaniz, S., Rio-Torto, I., Schulz, E., & Akata, Z. (2023). In-context
impersonation reveals large language models' strengths and biases. NeurIPS 2023.
https://arxiv.org/abs/2305.14930

Sclar, M., Choi, Y., Tsvetkov, Y., & Suhr, A. (2023). Quantifying language models' sensitivity
to spurious features in prompt design, or: How I learned to start worrying about prompt
formatting. ICLR 2024. https://arxiv.org/abs/2310.11324

Sharma, M., et al. (2023). Towards understanding sycophancy in language models.
arXiv:2310.13548. https://arxiv.org/abs/2310.13548

Wang, P., et al. (2023). Large language models are not fair evaluators. arXiv:2305.17926.
https://arxiv.org/abs/2305.17926

Yin, Z., Wang, H., Horio, K., Kawahara, D., & Sekine, S. (2024). Should we respect LLMs? A
cross-lingual study on the influence of prompt politeness on LLM performance. arXiv:2402.14531.
https://arxiv.org/abs/2402.14531

Zheng, L., et al. (2023b). Judging LLM-as-a-judge with MT-Bench and Chatbot Arena. NeurIPS 2023
Datasets and Benchmarks. https://arxiv.org/abs/2306.05685

Zheng, M., Pei, J., Logeswaran, L., Lee, M., & Jurgens, D. (2023). When "a helpful assistant"
is not really helpful: Personas in system prompts do not improve performances of large language
models. Findings of EMNLP 2024. https://arxiv.org/abs/2311.10054

