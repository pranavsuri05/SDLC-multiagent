<<<<<<< HEAD
# BA Agent — Phase 1 (SOW → BRD)

This is **Phase 1** of the AI-powered SDLC platform: a single AI Agent (the
**Business Analyst Agent**) that turns an uploaded Statement of Work (SOW)
into a Business Requirement Document (BRD), with manual editing, AI-assisted
refinement, full version history, final-version locking, and Word export.

No databases, no LangGraph, no other agents — just this one, done properly.

---

## 1. Prerequisites

You need:

1. **Python 3.11 or newer** installed.
   - Check with: `python --version` (Windows) or `python3 --version` (Mac/Linux)
   - If not installed: https://www.python.org/downloads/ (on Windows, tick
     "Add Python to PATH" during install).
2. **VS Code** installed, with the **Python extension** (from the Extensions
   tab, search "Python", install the Microsoft one).
3. A **Google Gemini API key** (free tier available):
   - Go to https://aistudio.google.com/app/apikey
   - Sign in with a Google account, click "Create API key", copy it.

---

## 2. Project Setup (do this once)

Open the project folder in VS Code (`File → Open Folder…` → select
`sdlc-ba-agent`), then open a terminal inside VS Code
(`Terminal → New Terminal`) and run the following, one line at a time.

### Step 2.1 — Create a virtual environment

A virtual environment keeps this project's Python packages separate from
everything else on your machine.

**Windows (PowerShell):**
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```
If PowerShell blocks the activation script, run this once first:
```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

**Mac / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

You'll know it worked because your terminal prompt now starts with `(venv)`.

> You must run the activation command every time you open a new terminal to
> work on this project.

### Step 2.2 — Install dependencies

```bash
pip install -r requirements.txt
```

This installs Streamlit (UI), LangChain + Gemini SDK (AI), python-docx and
PyMuPDF (file parsing/export), and pydantic (config/validation).

### Step 2.3 — Configure your API key

1. Copy `.env.example` to a new file named `.env` in the project root.
   - Windows: `copy .env.example .env`
   - Mac/Linux: `cp .env.example .env`
2. Open `.env` in VS Code and replace `your_gemini_api_key_here` with the
   real API key you copied from Google AI Studio.
3. Save the file. **Never commit `.env` to git** — it contains your secret key.

---

## 3. Running the App

With your virtual environment activated (prompt shows `(venv)`):

```bash
streamlit run app/ui/streamlit_app.py
```

Your browser should open automatically to `http://localhost:8501`. If not,
open that URL manually.

To stop the app, go back to the terminal and press `Ctrl + C`.

---

## 4. Using the App

1. **Tab 1 — Upload & Generate**
   - Fill in Project Name, Client Name, Project Type, Industry.
   - Upload a `.docx`, `.pdf`, or `.txt` SOW file.
   - Click **Generate BRD**. This extracts the text, cleans it, and sends it
     to Gemini to produce BRD Version 1.

2. **Tab 2 — Review, Edit & Finalize**
   - View the generated BRD in an editable text box.
   - **Manual Edit**: change the text directly, click "Save Manual Edit" →
     creates a new version.
   - **AI Refine**: type an instruction like *"Add Multi-Factor
     Authentication"* or *"Replace MySQL with PostgreSQL"*, click
     "Refine with AI" → Gemini updates only the relevant sections and a new
     version is created.
   - **Sidebar**: browse all past versions, view any of them, or mark one as
     the **Final BRD** (locks it from further edits).
   - **Download**: click "Prepare .docx for download" then
     "Download BRD.docx" to get a professionally formatted Word document.

3. **Start New Project** (sidebar button) resets the session so you can
   upload a different SOW. Each project's version history is saved under
   `outputs/<project_id>/versions.json`.

---

## 5. Project Structure

```
sdlc-ba-agent/
  app/
    agents/
      business_analyst/
        agent.py             <- Gemini/LangChain wrapper (generate + refine)
        service.py           <- orchestrates parsing -> cleaning -> agent -> versions
        prompt_manager.py    <- loads & renders prompt templates (no hardcoded prompts)
        prompts/
          generate_brd.txt
          refine_brd.txt
    parsers/
      detector.py            <- detects .docx / .pdf / .txt
      docx_parser.py
      pdf_parser.py
      text_parser.py
      text_cleaner.py        <- preprocessing (removes headers/footers/page numbers)
    document_generator/
      brd_generator.py       <- markdown BRD -> formatted .docx
    services/
      version_service.py     <- version history (JSON file per project, no DB yet)
    utils/
      config.py              <- reads .env via pydantic-settings
      logger.py               <- centralized logging to logs/app.log
    ui/
      streamlit_app.py       <- the UI, calls the service layer only
  uploads/                   <- uploaded SOW files land here
  outputs/                   <- generated BRDs + exported .docx files
  logs/                      <- app.log (rotating)
  requirements.txt
  .env.example
```

---

## 6. Troubleshooting

- **`ValidationError: google_api_key Field required`** — you haven't created
  `.env` yet, or it's missing `GOOGLE_API_KEY`. See Step 2.3.
- **`streamlit: command not found`** — your virtual environment isn't
  activated. Re-run the activation command from Step 2.1.
- **Gemini errors about quota/rate limit** — the free tier has request
  limits; wait a minute and try again, or check your usage at
  https://aistudio.google.com.
- **Uploaded PDF produces empty/garbled text** — if the PDF is a scanned
  image (not real text), PyMuPDF can't extract it; this Phase 1 build
  doesn't include OCR. Use a text-based PDF, DOCX, or TXT instead.

---

## 7. What's Deliberately NOT in Phase 1

Per scope, this build does **not** include: HLD/LLD generation, User Story or
Test Case generation, LangGraph multi-agent orchestration, a real database,
authentication/multi-user support, or the Solution Architect Agent. Those are
Phase 2+.
=======
# ai-sdlc



## Getting started

To make it easy for you to get started with GitLab, here's a list of recommended next steps.

Already a pro? Just edit this README.md and make it your own. Want to make it easy? [Use the template at the bottom](#editing-this-readme)!

## Add your files

* [Create](https://docs.gitlab.com/user/project/repository/web_editor/#create-a-file) or [upload](https://docs.gitlab.com/user/project/repository/web_editor/#upload-a-file) files
* [Add files using the command line](https://docs.gitlab.com/topics/git/add_files/#add-files-to-a-git-repository) or push an existing Git repository with the following command:

```
cd existing_repo
git remote add origin https://gitlab.com/project-aiml/ai-sdlc.git
git branch -M main
git push -uf origin main
```

## Integrate with your tools

* [Set up project integrations](https://gitlab.com/project-aiml/ai-sdlc/-/settings/integrations)

## Collaborate with your team

* [Invite team members and collaborators](https://docs.gitlab.com/user/project/members/)
* [Create a new merge request](https://docs.gitlab.com/user/project/merge_requests/creating_merge_requests/)
* [Automatically close issues from merge requests](https://docs.gitlab.com/user/project/issues/managing_issues/#closing-issues-automatically)
* [Enable merge request approvals](https://docs.gitlab.com/user/project/merge_requests/approvals/)
* [Set auto-merge](https://docs.gitlab.com/user/project/merge_requests/auto_merge/)

## Test and Deploy

Use the built-in continuous integration in GitLab.

* [Get started with GitLab CI/CD](https://docs.gitlab.com/ci/quick_start/)
* [Analyze your code for known vulnerabilities with Static Application Security Testing (SAST)](https://docs.gitlab.com/user/application_security/sast/)
* [Deploy to Kubernetes, Amazon EC2, or Amazon ECS using Auto Deploy](https://docs.gitlab.com/topics/autodevops/requirements/)
* [Use pull-based deployments for improved Kubernetes management](https://docs.gitlab.com/user/clusters/agent/)
* [Set up protected environments](https://docs.gitlab.com/ci/environments/protected_environments/)

***

# Editing this README

When you're ready to make this README your own, just edit this file and use the handy template below (or feel free to structure it however you want - this is just a starting point!). Thanks to [makeareadme.com](https://www.makeareadme.com/) for this template.

## Suggestions for a good README

Every project is different, so consider which of these sections apply to yours. The sections used in the template are suggestions for most open source projects. Also keep in mind that while a README can be too long and detailed, too long is better than too short. If you think your README is too long, consider utilizing another form of documentation rather than cutting out information.

## Name
Choose a self-explaining name for your project.

## Description
Let people know what your project can do specifically. Provide context and add a link to any reference visitors might be unfamiliar with. A list of Features or a Background subsection can also be added here. If there are alternatives to your project, this is a good place to list differentiating factors.

## Badges
On some READMEs, you may see small images that convey metadata, such as whether or not all the tests are passing for the project. You can use Shields to add some to your README. Many services also have instructions for adding a badge.

## Visuals
Depending on what you are making, it can be a good idea to include screenshots or even a video (you'll frequently see GIFs rather than actual videos). Tools like ttygif can help, but check out Asciinema for a more sophisticated method.

## Installation
Within a particular ecosystem, there may be a common way of installing things, such as using Yarn, NuGet, or Homebrew. However, consider the possibility that whoever is reading your README is a novice and would like more guidance. Listing specific steps helps remove ambiguity and gets people to using your project as quickly as possible. If it only runs in a specific context like a particular programming language version or operating system or has dependencies that have to be installed manually, also add a Requirements subsection.

## Usage
Use examples liberally, and show the expected output if you can. It's helpful to have inline the smallest example of usage that you can demonstrate, while providing links to more sophisticated examples if they are too long to reasonably include in the README.

## Support
Tell people where they can go to for help. It can be any combination of an issue tracker, a chat room, an email address, etc.

## Roadmap
If you have ideas for releases in the future, it is a good idea to list them in the README.

## Contributing
State if you are open to contributions and what your requirements are for accepting them.

For people who want to make changes to your project, it's helpful to have some documentation on how to get started. Perhaps there is a script that they should run or some environment variables that they need to set. Make these steps explicit. These instructions could also be useful to your future self.

You can also document commands to lint the code or run tests. These steps help to ensure high code quality and reduce the likelihood that the changes inadvertently break something. Having instructions for running tests is especially helpful if it requires external setup, such as starting a Selenium server for testing in a browser.

## Authors and acknowledgment
Show your appreciation to those who have contributed to the project.

## License
For open source projects, say how it is licensed.

## Project status
If you have run out of energy or time for your project, put a note at the top of the README saying that development has slowed down or stopped completely. Someone may choose to fork your project or volunteer to step in as a maintainer or owner, allowing your project to keep going. You can also make an explicit request for maintainers.
>>>>>>> 3c5eb8c740b7cea295858d8e095d732d6a346bea
