# SBNote - Scrap Binding Notebook

A self-hosted, database-less note-taking web app that utilises a flat folder of markdown files for storage. SBNote is a fork of [flatnote](https://github.com/Dullage/flatnote) with enhanced features for organizing content through tags and scraps.

## File Structure

SBNote organizes files in the following structure within the `SBNOTE_PATH` directory:
- `notes/` - Contains all markdown files
- `files/` - Contains uploaded attachments
- `index/` - Contains search index files

## Design Principle

SBNote is designed to be a distraction-free note-taking app that emphasizes content organization through a unique scrap-based workflow. This means:

* A clean and simple user interface that focuses on content creation and organization.
* A flexible system where you can create individual scraps (fragments) of content and organize them through tags.
* Tags serve as the primary organizational tool, allowing you to group related scraps and bind them into cohesive notebooks.
* Quick access to a full-text search from anywhere in the app (keyboard shortcut "/").

Another key design principle is not to take your notes hostage. Your notes are just markdown files. There's no database, proprietary formatting, complicated folder structures or anything like that. You're free at any point to just move the files elsewhere and use another app.

Equally, the only thing SBNote caches is the search index and that's incrementally synced on every search (and when SBNote first starts). This means that you're free to add, edit & delete the markdown files outside of SBNote even whilst SBNote is running.

## Enhanced Features

Building upon flatnote's foundation, SBNote introduces a unique organizational system inspired by Japanese illustrator Noritake's "SBN - Super Binding Notebook" concept - a simple idea of binding papers together to create notebooks:

* **Tag-based Scrap Organization**: Tags serve as a way to group scraps (fragments) of content, which can then be bound together to form notebooks.
* **Scrap-to-Notebook Workflow**: Create individual scraps with tags, then organize them into cohesive notebooks based on your tagging system.
* **Flexible Content Addition**: Like the physical SBN where you can add any paper by folding it in half, SBNote allows you to freely add and organize content without rigid rules.

## Getting Started

### Self Hosted

If you'd prefer to host SBNote yourself then the recommendation is to use Docker.

### Example Docker Run Command

```shell
docker run -d \
  -e "PUID=1000" \
  -e "PGID=1000" \
  -e "SBNOTE_AUTH_TYPE=password" \
  -e "SBNOTE_USERNAME=user" \
  -e 'SBNOTE_PASSWORD=changeMe!' \
  -e "SBNOTE_SECRET_KEY=aLongRandomSeriesOfCharacters" \
  -v "$(pwd)/data:/data" \
  -p "8080:8080" \
  yamnor/sbnote:latest
```

### Example Docker Compose
```yaml
services:
  sbnote:
    container_name: sbnote
    image: yamnor/sbnote:latest
    environment:
      PUID: 1000
      PGID: 1000
      SBNOTE_AUTH_TYPE: "password"
      SBNOTE_USERNAME: "user"
      SBNOTE_PASSWORD: "changeMe!"
      SBNOTE_SECRET_KEY: "aLongRandomSeriesOfCharacters"
    volumes:
      - "./data:/data"
      # Optional. Allows you to save the search index in a different location: 
      # - "./index:/data/index"
    ports:
      - "8080:8080"
    restart: unless-stopped
```

## Acknowledgments

SBNote is a fork of [flatnote](https://github.com/Dullage/flatnote) by Dullage. The enhanced tag-based organization system is inspired by Japanese illustrator Noritake's "SBN - Super Binding Notebook" concept - a simple yet powerful idea of binding papers together to create notebooks without rigid rules, allowing for flexible content organization.

## Thanks

A special thanks to the fantastic open-source projects that make SBNote possible.

* [flatnote](https://github.com/Dullage/flatnote) - The original note-taking app that SBNote is based on.
* [Whoosh](https://whoosh.readthedocs.io/en/latest/intro.html) - A fast, pure Python search engine library.
* [TOAST UI Editor](https://ui.toast.com/tui-editor) - A GFM Markdown and WYSIWYG editor for the browser.
