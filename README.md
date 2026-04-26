# media-finder
-A lightweight desktop app to scan folders, filter files by type, and copy them into organised subfolders — all through a simple GUI. No terminal commands. No pasting scripts.

-Built with Python and Tkinter

-What it does(*Scans a folder and all its subfolders recursively,*Filters files by extension across 4 built-in sections — Photos, Videos, Audio, Documents,*Lets you add your own extensions to any section ,*Lets you create entirely new section,*Copies matched files into clean, organised subfolders at a destination you choose,*Auto-renames duplicates so nothing gets overwritten

=Requirements-
Python 3.x,*Tkinter

=How to use

-1. Set your source folder

Click **BROWSE** next to SOURCE and pick the folder you want to scan. It will search every subfolder inside it automatically.

-2. Set your destination folder

Click **BROWSE** next to DEST and pick where you want the organised files to be copied. Subfolders like `/photos/`, `/videos/` etc. will be created here automatically.

-3. Choose your file types

=The app has 4 built-in sections — each with a default set of extensions pre-ticked:

  Photos-.jpg .jpeg .png .gif .bmp .tiff .heic .webp .raw .cr2 .nef .arw |
  Videos-.mp4 .mov .avi .mkv .wmv .m4v .flv .3gp .ts .mts |
  Audio-.mp3 .wav .flac .aac .ogg .wma .m4a .aiff .opus |
  Documents-.docx .doc .pdf .txt .odt .rtf .xlsx .xls .pptx .csv |
  
Tick or untick any extension. Untick the section header checkbox entirely to skip that section.

-4. Add custom extensions

Each section has a small input box at the bottom. Type an extension like /and hit **ADD** or press Enter. It appears instantly as a checkbox. You can type multiple at once separated by commas — `vcd, vob, mpg`.

-5. Create a new section

At the very bottom of the window is a **NEW SECTION** bar. Type a name like `jliy` and click **CREATE**. A blank section appears as a new column with its own extension input. Add `.psd`, `.ai`, `.indd` etc. using the autocomplete input. Files matched in this section will be copied to a  subfolder.

-6. Scan

Click **SCAN**. The results panel will fill with every matched file, labelled by which section it belongs to. Review this list before doing anything else.

-7. Copy

Once you are happy with the scan results, click **COPY**. Files are copied (not moved) into organised subfolders at your destination
-------

/your-destination/
  /photos/
  /videos/
  /audio/
  /documents/
  /hujg/         ← if you created this section
-----
If two files share the same name, the second one is automatically renamed (e.g. `photo_1.jpg`) so nothing is overwritten.

-8. Clear

Click **CLEAR** to wipe the results list and start fresh.

=Notes
- Files are **copied**, not moved. Your source folder is never modified.
- Always review the scan results before copying. What you see is exactly what gets copied.
