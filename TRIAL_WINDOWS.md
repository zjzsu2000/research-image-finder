# Windows trial

This is an unsigned prototype. Windows or antivirus software may warn on first launch. Passing
Windows CI/build checks does not mean the GUI has completed an interactive Windows user test.
The artifact needs no Python, pip, Git, installer, or command-line setup. Application processing
stays local and does not upload images or use network services.

1. Download the `ResearchImageFinder-windows-x64` artifact and unzip it.
2. Double-click `ResearchImageFinder.exe`.
3. Select one query image and one authorized local folder or drive.
4. Click **Start Search** and review the ranked candidates.
5. Treat every candidate as a suggestion requiring human confirmation. No candidate does not
   prove that the source is absent.

The application has no installer or updater. To remove it completely, close it and delete the
unzipped folder or executable.
