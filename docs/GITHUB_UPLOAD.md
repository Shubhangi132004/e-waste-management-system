# GitHub upload guide

Review the project before publishing:

```powershell
git status
git grep -n -I -E "Pass@|password=|SECRET_KEY=|postgresql.*:" -- ':!.env.example'
```

Confirm that `.env`, `uploads/`, caches, logs, database dumps, and test artifacts are ignored. Then create a repository on GitHub without inventing an owner URL and run:

```powershell
git init
git add .
git commit -m "Upgrade EcoSmart e-waste management system"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
```

Replace the placeholder only with your own repository URL. Do not push credentials, personal addresses, real uploaded images, or database dumps.
