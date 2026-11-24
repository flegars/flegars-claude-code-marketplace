import json
import os
import re
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
SKILL_DIR = Path(__file__).resolve().parents[1]
PLUGIN_DIR = SKILL_DIR.parents[1]
SCRIPTS = SKILL_DIR / "scripts"
sys.path.insert(0, str(SCRIPTS))

from prr.adapters.ado import AzureDevOpsAdapter, parse_remote as ado_remote  # noqa: E402
from prr.adapters.github import GitHubAdapter  # noqa: E402
from prr.adapters.gitlab import GitLabAdapter  # noqa: E402
from prr.core import regression  # noqa: E402
from prr.core.diff import locate, parse_unified_diff  # noqa: E402
from prr.core.review import ReviewError, build_review, marker, parse_marker  # noqa: E402
from prr.detect import detect  # noqa: E402

DIFF = """diff --git a/src/a.php b/src/a.php
index 111..222 100644
--- a/src/a.php
+++ b/src/a.php
@@ -1,5 +1,6 @@
 line1
-line2
+line2 bis
+line2 ter
 line3
 line4
 line5
@@ -20,3 +21,3 @@ function foo()
 line20
-line21
+line21 bis
 line22
diff --git a/old.txt b/new.txt
similarity index 90%
rename from old.txt
rename to new.txt
--- a/old.txt
+++ b/new.txt
@@ -1,2 +1,2 @@
-x
+y
 z
diff --git a/gone.php b/gone.php
deleted file mode 100644
--- a/gone.php
+++ /dev/null
@@ -1,2 +0,0 @@
-a
-b
"""

FILES = parse_unified_diff(DIFF)


def comment(path="src/a.php", start=2, end=None, side="RIGHT", severity="important", category="generic", rule=None):
    return {"path": path, "line_start": start, "line_end": end or start, "side": side, "severity": severity,
            "category": category, "body": {"problem": "p", "justification": "j", "proposal": "x"}, "rule_ref": rule}


def review_of(comments, existing=(), max_inline=15):
    raw = {"comments": comments, "summary": {"us": {"found": False}, "claude_md_loaded": [], "notes": []}}
    return build_review(raw, FILES, [], [], set(existing), max_inline)


GITHUB_CONTEXT = {"platform": "github", "number": 7, "head_sha": "h" * 40, "diff": DIFF,
                  "native": {"owner": "o", "repo": "r"}}
ADO_CONTEXT = {"platform": "ado", "number": 7, "head_sha": "h" * 40, "diff": DIFF,
               "native": {"org_url": "https://dev.azure.com/org",
                          "route": {"project": "P", "repositoryId": "rid", "pullRequestId": 7},
                          "iteration": 3, "change_tracking": {"src/a.php": 11}}}
GITLAB_CONTEXT = {"platform": "gitlab", "number": 7, "head_sha": "h" * 40, "diff": DIFF,
                  "native": {"project": "g%2Fr", "project_path": "g/r",
                             "diff_refs": {"base_sha": "b", "start_sha": "s", "head_sha": "h"}}}
NO_EXISTING = {"summary": None, "comments": []}


class DiffTest(unittest.TestCase):
    def test_right_side_lines(self):
        right = FILES["src/a.php"].right
        self.assertEqual(right[2].kind, "added")
        self.assertEqual(right[4].kind, "context")
        self.assertEqual((right[4].old_line, right[4].new_line), (3, 4))
        self.assertEqual(right[22].kind, "added")
        self.assertNotIn(10, right)

    def test_rename_and_delete(self):
        self.assertEqual(FILES["new.txt"].old_path, "old.txt")
        self.assertIsNone(FILES["gone.php"].new_path)
        self.assertEqual(FILES["gone.php"].left[2].kind, "deleted")

    def test_range_must_stay_in_one_hunk(self):
        self.assertIsNotNone(locate(FILES, "src/a.php", 1, 6, "RIGHT"))
        self.assertIsNone(locate(FILES, "src/a.php", 5, 22, "RIGHT"))
        self.assertIsNone(locate(FILES, "src/a.php", 10, 10, "RIGHT"))


class ReviewTest(unittest.TestCase):
    def test_out_of_diff_goes_to_summary(self):
        review = review_of([comment(start=10)])
        self.assertEqual(review["comments"], [])
        self.assertEqual(review["summary"]["not_postable_inline"][0]["reason"], "out_of_diff")

    def test_cap_keeps_most_severe(self):
        review = review_of([comment(start=1, severity="suggestion"), comment(start=2, severity="bloquant"),
                            comment(start=3, severity="question")], max_inline=1)
        self.assertEqual([c["severity"] for c in review["comments"]], ["bloquant"])
        self.assertEqual({i["reason"] for i in review["summary"]["not_postable_inline"]}, {"over_cap"})
        self.assertEqual(review["verdict"], "blocking")

    def test_existing_fingerprint_is_not_reposted(self):
        first = review_of([comment(start=2)])
        fp = first["comments"][0]["fingerprint"]
        second = review_of([comment(start=2)], existing={fp})
        self.assertEqual(second["comments"], [])
        self.assertEqual(second["summary"]["already_posted"], 1)

    def test_rule_category_requires_rule_ref(self):
        with self.assertRaises(ReviewError):
            review_of([comment(category="rule")])

    def test_marker_roundtrip(self):
        self.assertEqual(parse_marker("x\n" + marker("comment", "abc")), {"kind": "comment", "fp": "abc"})
        self.assertIsNone(parse_marker("<!-- autre -->"))


class GitHubPayloadTest(unittest.TestCase):
    adapter = GitHubAdapter(Path("."))

    def test_single_review_with_range(self):
        review = review_of([comment(start=1, end=3)])
        payloads = self.adapter.build_payloads(review, GITHUB_CONTEXT, NO_EXISTING, request_changes=False)
        self.assertEqual([p["step"] for p in payloads], ["create_review", "create_summary"])
        body = payloads[0]["body"]
        self.assertEqual(body["event"], "COMMENT")
        self.assertEqual(body["commit_id"], "h" * 40)
        self.assertEqual({k: body["comments"][0][k] for k in ("path", "line", "start_line", "side")},
                         {"path": "src/a.php", "line": 3, "start_line": 1, "side": "RIGHT"})
        self.assertIn("pr-reviewer:v2 kind=comment", body["comments"][0]["body"])

    def test_summary_is_updated_not_duplicated(self):
        existing = {"summary": {"native_id": 99, "body": ""}, "comments": []}
        payloads = self.adapter.build_payloads(review_of([]), GITHUB_CONTEXT, existing, request_changes=False)
        self.assertEqual([(p["step"], p["method"]) for p in payloads], [("update_summary", "PATCH")])
        self.assertTrue(payloads[0]["endpoint"].endswith("issues/comments/99"))

    def test_request_changes_only_with_flag_and_blocking(self):
        blocking = review_of([comment(severity="bloquant")])
        self.assertEqual(self.adapter.build_payloads(blocking, GITHUB_CONTEXT, NO_EXISTING, False)[0]["body"]["event"],
                         "COMMENT")
        self.assertEqual(self.adapter.build_payloads(blocking, GITHUB_CONTEXT, NO_EXISTING, True)[0]["body"]["event"],
                         "REQUEST_CHANGES")
        minor = review_of([comment(severity="suggestion")])
        self.assertEqual(self.adapter.build_payloads(minor, GITHUB_CONTEXT, NO_EXISTING, True)[0]["body"]["event"],
                         "COMMENT")


class AdoPayloadTest(unittest.TestCase):
    adapter = AzureDevOpsAdapter(Path("."))

    def test_thread_context(self):
        review = review_of([comment(start=1, end=3), comment(path="gone.php", start=2, side="LEFT")])
        payloads = self.adapter.build_payloads(review, ADO_CONTEXT, NO_EXISTING, request_changes=False)
        threads = [p["body"] for p in payloads if p["step"] == "create_thread"]
        right = next(t for t in threads if t["threadContext"]["filePath"] == "/src/a.php")
        self.assertEqual(right["threadContext"]["rightFileStart"], {"line": 1, "offset": 1})
        self.assertEqual(right["threadContext"]["rightFileEnd"], {"line": 3, "offset": 1})
        self.assertEqual(right["pullRequestThreadContext"]["changeTrackingId"], 11)
        left = next(t for t in threads if t["threadContext"]["filePath"] == "/gone.php")
        self.assertIn("leftFileStart", left["threadContext"])
        fingerprints = {c["path"]: c["fingerprint"] for c in review["comments"]}
        self.assertEqual(right["properties"]["pr-reviewer.fp"]["$value"], fingerprints["src/a.php"])

    def test_non_blocking_by_default(self):
        review = review_of([comment(severity="bloquant")])
        payloads = self.adapter.build_payloads(review, ADO_CONTEXT, NO_EXISTING, request_changes=False)
        self.assertTrue(all(p["body"]["status"] == "closed" for p in payloads if "body" in p and "status" in p["body"]))
        self.assertFalse(any("cli" in p for p in payloads))
        with_flag = self.adapter.build_payloads(review, ADO_CONTEXT, NO_EXISTING, request_changes=True)
        cli = with_flag[-1]["cli"]
        self.assertEqual(cli[cli.index("--vote") + 1], "wait-for-author")


class GitLabPayloadTest(unittest.TestCase):
    adapter = GitLabAdapter(Path("."))

    def test_positions(self):
        review = review_of([comment(start=2), comment(start=4), comment(path="gone.php", start=1, side="LEFT")])
        payloads = self.adapter.build_payloads(review, GITLAB_CONTEXT, NO_EXISTING, request_changes=False)
        positions = {(p["body"]["position"].get("new_line"), p["body"]["position"].get("old_line"))
                     for p in payloads if p["step"] == "create_discussion"}
        self.assertEqual(positions, {(2, None), (4, 3), (None, 1)})
        first = next(p for p in payloads if p["step"] == "create_discussion")["body"]["position"]
        self.assertEqual((first["base_sha"], first["start_sha"], first["head_sha"], first["position_type"]),
                         ("b", "s", "h", "text"))

    def test_request_changes_only_with_flag(self):
        review = review_of([comment(severity="bloquant")])
        steps = [p["step"] for p in self.adapter.build_payloads(review, GITLAB_CONTEXT, NO_EXISTING, False)]
        self.assertNotIn("request_changes", steps)
        steps = [p["step"] for p in self.adapter.build_payloads(review, GITLAB_CONTEXT, NO_EXISTING, True)]
        self.assertIn("request_changes", steps)


class NeverApproveTest(unittest.TestCase):
    def test_no_adapter_can_approve(self):
        review = review_of([comment(severity="bloquant")])
        for adapter, context in ((GitHubAdapter(Path(".")), GITHUB_CONTEXT), (AzureDevOpsAdapter(Path(".")), ADO_CONTEXT),
                                 (GitLabAdapter(Path(".")), GITLAB_CONTEXT)):
            for flag in (False, True):
                dumped = json.dumps(adapter.build_payloads(review, context, NO_EXISTING, flag))
                self.assertNotIn("APPROVE", dumped)
                self.assertNotRegex(dumped, r'"approve|"vote": (10|5)|/approve')
        sources = " ".join(p.read_text() for p in (SCRIPTS / "prr" / "adapters").glob("*.py"))
        self.assertNotIn('"APPROVE"', sources)
        self.assertNotRegex(sources, r'"approve"|"approve-with-suggestions"|merge_requests/[^"]*/approve')


class CoreIsPlatformAgnosticTest(unittest.TestCase):
    FORBIDDEN = re.compile(r"\b(gh|az|glab)\b|api\.github|github\.com|dev\.azure|visualstudio\.com|gitlab\.com"
                           r"|/_apis/|/api/v4", re.IGNORECASE)

    def test_core_has_no_platform_reference(self):
        targets = [*(SCRIPTS / "prr" / "core").glob("*.py"), PLUGIN_DIR / "agents" / "pr-reviewer.md",
                   SKILL_DIR / "references" / "review-format.md", SKILL_DIR / "references" / "review-rules.md"]
        for path in targets:
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                self.assertIsNone(self.FORBIDDEN.search(line), f"{path.name}:{number} : {line.strip()}")


class DetectTest(unittest.TestCase):
    def test_remote_hosts(self):
        cases = {
            "git@github.com:o/r.git": "github",
            "https://github.com/o/r": "github",
            "https://org@dev.azure.com/org/Projet/_git/repo": "ado",
            "git@ssh.dev.azure.com:v3/org/Projet/repo": "ado",
            "https://org.visualstudio.com/Projet/_git/repo": "ado",
            "git@gitlab.com:groupe/sous/r.git": "gitlab",
            "git@git.mon-entreprise.fr:o/r.git": "local",
        }
        for url, expected in cases.items():
            self.assertEqual(detect(None, {}, None, url)["platform"], expected, url)
        self.assertEqual(detect(None, {}, None, None)["platform"], "local")

    def test_precedence(self):
        config = {"platform": "gitlab", "host": "git.mon-entreprise.fr"}
        self.assertEqual(detect(None, config, None, "git@github.com:o/r.git")["platform"], "gitlab")
        self.assertEqual(detect("local", config, None, "git@github.com:o/r.git")["platform"], "local")
        self.assertEqual(detect(None, {}, "https://gitlab.com/g/r/-/merge_requests/3", None)["platform"], "gitlab")

    def test_ado_remote_parts(self):
        self.assertEqual(ado_remote("https://dev.azure.com/org/Mon%20Projet/_git/repo.git")["project"], "Mon Projet")


def _git(cwd, *args, env=None):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, env=env)


class LocalEndToEndTest(unittest.TestCase):
    def test_local_mode_without_remote_or_auth(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
                   "GIT_COMMITTER_EMAIL": "t@t", "PATH": "/usr/bin:/bin"}
            _git(repo, "init", "-q", "-b", "main", env=env)
            (repo / "CLAUDE.md").write_text("Pas de var_dump.\n")
            (repo / "src").mkdir()
            (repo / "src" / "x.php").write_text("a\nb\nc\n")
            _git(repo, "add", ".", env=env)
            _git(repo, "commit", "-qm", "init", env=env)
            (repo / "src" / "x.php").write_text("a\nb corrigé\nc\n")
            _git(repo, "commit", "-qam", "fix(x): corrige b (#42)", env=env)
            _git(repo, "switch", "-qc", "feat/y", env=env)
            (repo / "src" / "x.php").write_text("a\nb2\nc\nvar_dump(1);\n")
            _git(repo, "commit", "-qam", "feat: y", env=env)

            prr = [sys.executable, str(SCRIPTS / "prr.py")]
            collected = json.loads(subprocess.run([*prr, "collect"], cwd=repo, env=env, capture_output=True,
                                                  text=True, check=True).stdout)
            self.assertEqual(collected["platform"], "local")
            self.assertEqual(collected["claude_md"], ["CLAUDE.md"])
            self.assertEqual(collected["regression_risks"], 1)
            Path(collected["agent_review_file"]).write_text(json.dumps({
                "comments": [comment(path="src/x.php", start=4, severity="bloquant", category="rule",
                                     rule={"file": "CLAUDE.md", "rule": "Pas de var_dump."})],
                "summary": {"us": {"found": False}, "claude_md_loaded": ["CLAUDE.md"], "notes": []}}))
            published = json.loads(subprocess.run([*prr, "publish", "--work-dir", collected["work_dir"]], cwd=repo,
                                                  env=env, capture_output=True, text=True, check=True).stdout)
            self.assertEqual(published["mode"], "local")
            self.assertEqual(published["verdict"], "blocking")
            self.assertEqual(published["counts"]["question"], 1)
            report = Path(published["files"]["markdown"]).read_text()
            self.assertIn("src/x.php:4", report)
            self.assertIn("(PR #42)", report)
            neutral = json.loads(Path(published["files"]["json"]).read_text())
            self.assertEqual(neutral["schema"], "pr-reviewer/review@2")


class RegressionTest(unittest.TestCase):
    def test_fix_detection(self):
        self.assertTrue(regression.is_fix("fix(api): corrige le calcul (#12)"))
        self.assertTrue(regression.is_fix("hotfix: urgence"))
        self.assertTrue(regression.is_fix("Merged PR 123: fix: plantage"))
        self.assertTrue(regression.is_fix("Merge pull request #5 from org/hotfix/plantage"))
        self.assertFalse(regression.is_fix("feat: prefix fix"))
        self.assertEqual(regression.references("fix: x (#12)"), "PR #12")
        self.assertEqual(regression.references("Merged PR 123: fix"), "PR 123")
        self.assertIsNone(regression.references("fix: rien"))

    def test_window_disabled(self):
        self.assertEqual(regression.scan(FILES, "HEAD", Path("."), 0, now=time.time()), [])


if __name__ == "__main__":
    unittest.main()
