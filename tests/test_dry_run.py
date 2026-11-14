import re

from conftest import FIXTURE_TASKS, ROOT, model, run_cli


def numbers(text):
    return [float(x) for x in re.findall(r"\d+(?:\.\d+)?", text.replace(",", ""))]


def has_number(text, value, tol=1e-6):
    return any(abs(n - value) <= tol for n in numbers(text))


def test_dry_run_makes_no_network_call_and_prints_total(tmp_path):
    attempts = tmp_path / "net_attempts.log"
    result = run_cli(
        "--tasks", str(FIXTURE_TASKS),
        "--config", str(ROOT / "config" / "models.yaml"),
        "--dry-run",
        block_network=True,
        net_log=attempts,
    )
    assert result.returncode == 0, result.stderr
    assert "total" in result.stdout.lower()
    assert not attempts.exists() or attempts.read_text() == "", attempts.read_text()


def test_dry_run_multiplies_versions_samples_models_and_judges_pairwise_only(make_config):
    # Input prices are zero, so cost depends only on max_tokens x output price.
    # Fixtures: 4 tasks, 1 of them pairwise. samples = 2.
    # Model a: 4 tasks x 5 versions x 2 samples = 40 calls x 100 tok x $10/Mtok  = 0.04
    # Model b: 40 calls x 200 tok x $20/Mtok                                      = 0.16
    # Judge: 1 pairwise x 2 models x 4 styles x 2 samples x 2 orders x 1 judge
    #        = 32 calls x 300 tok x $50/Mtok                                      = 0.48
    # Total 0.68.
    config = make_config(
        [model("a", 100, price_out=10), model("b", 200, price_out=20)],
        [model("j", 300, price_out=50)],
    )
    result = run_cli("--tasks", str(FIXTURE_TASKS), "--config", str(config), "--dry-run")
    assert result.returncode == 0, result.stderr
    out = result.stdout
    assert has_number(out, 40)
    for cost in (0.04, 0.16, 0.48, 0.68):
        assert has_number(out, cost), f"{cost} missing from:\n{out}"


def test_dry_run_charges_local_token_count_of_every_prompt_at_input_price(make_config):
    import litellm
    import yaml

    config = make_config([model("a", 1, price_in=10000)], [], samples=1)
    tokens = sum(
        litellm.token_counter(model="openai/a", text=text)
        for f in FIXTURE_TASKS.glob("*.yaml")
        for text in yaml.safe_load(f.read_text())["versions"].values()
    )
    result = run_cli("--tasks", str(FIXTURE_TASKS), "--config", str(config), "--dry-run")
    assert result.returncode == 0, result.stderr
    assert has_number(result.stdout, tokens * 10000 / 1e6, tol=0.01)
