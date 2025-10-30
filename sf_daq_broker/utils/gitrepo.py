from pathlib import Path
from git import Repo, InvalidGitRepositoryError


class GitRepo:

    def __init__(self, url, path):
        self.url = url
        self.path = path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        self.repo = get_or_clone_repo(url, path)

    def update(self):
        self.check_clean()
        self.repo.git.pull("--rebase")

    def check_clean(self):
        if self.repo.is_dirty(untracked_files=True):
            status = self.repo.git.status()
            raise OhMyGit(f"the local copy is not clean:\n{status}")

    def clean(self):
        g = self.repo.git
        g.fetch()
        g.reset("--hard", "HEAD")
        g.clean("-fdx") # force remove untracked/ignored files/directories

    def commit(self, fname, message=None):
        if message is None:
            operation = "Updated" if self.is_tracked(fname) else "Added"
            message = f"{operation} {fname}"
        file_path = self.path / fname
        self.repo.index.add([file_path])
        self.repo.index.commit(message)
        self.repo.remote().push()

    def is_tracked(self, fname):
        entries = set(path for path, _stage in self.repo.index.entries.keys())
        return fname in entries

    def __repr__(self):
        tn = type(self).__name__
        return f'{tn}("{self.url}", "{self.path}")'



def get_or_clone_repo(url, path):
    try:
        return Repo(path)
    except InvalidGitRepositoryError:
        return Repo.clone_from(url, path)



class OhMyGit(RuntimeError):
    pass





if __name__ == "__main__":
    import shutil


    def try_update(repo):
        try:
            repo.update()
        except Exception as e:
            en = type(e).__name__
            print("Caught expected error:")
            print(f"{en}: {e}")
        else:
            raise RuntimeError("expected error did not raise")


    url = "git@gitea.psi.ch:augustin_s/test.git"
    path = "/tmp/test_repo"

    path = Path(path)
    if path.exists():
        shutil.rmtree(path)

    git = GitRepo(url, path)
    git.update()


    contamination = path / "contamination"
    contamination.write_text("I am untracked")

    try_update(git)

    contamination.unlink()

    git.update()


    existing = path / "existing"
    existing.write_text("I was changed")

    try_update(git)



