# OSX_Forensics

Includes scripts investigating OSX systems.

## Change process

### Creating Tools

Create a new folder, add a small README.md saying what it does or why.

Create a requirements.txt with whatever python libraries your code needs.

### Modifying Tools

If you add a new 3rd-party import, update the requirements.txt in the same folder.

### Committing your changes

Create a local branch with a unique name:
```shell
git checkout -b myChange
```

Stage and commit your changes:
```shell
git add -ip
git commit -m "Some small message here"
```

Push your branch to the remote:
```shell
git push --set-upstream origin myChange
```

Create a [pull request](https://github.com/Omen-Cyber/OSX_Forensics/pulls).

Get someone to review and approve it.

Merge it.