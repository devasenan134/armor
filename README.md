# armor

My portfolio site, live at [armor.craftingtable.cc](https://armor.craftingtable.cc).

It has two editions:

- **`/`**: the main portfolio. Dark/light theme, my work, experience and home lab.
- **`/minecraft/`**: the same portfolio as a Minecraft-style world. Scrolling digs down through the layers, from the surface to bedrock.

Both are plain HTML, CSS and JavaScript with no build step. All the block textures and item sprites in the Minecraft edition are drawn in code at load time, so there are no game assets in this repo.

## Layout

```
site/        what gets served
  index.html           main portfolio
  minecraft/index.html Minecraft edition
  assets/icons/        tech logos (Simple Icons, CC0)
design/      drafts and earlier versions
deploy/      Caddy container for my home server
```

## Run locally

```sh
cd site && python3 -m http.server 8000
```

## Deploy

On the server:

```sh
cd ~/armor/deploy && docker compose up -d
```

Caddy serves `site/` on `127.0.0.1:8150`, and a Cloudflare tunnel route points `armor.craftingtable.cc` at it. To update, `git pull`; Caddy serves the new files immediately.

## Credits

- Tech logos from [Simple Icons](https://simpleicons.org) (CC0). Logos belong to their owners.
- Fonts: Geist and Geist Mono, Noto Sans and Silkscreen (Google Fonts). Monocraft (OFL) is used in one of the drafts.

The Minecraft edition is a fan-made design. Not an official Minecraft product. Not approved by or associated with Mojang or Microsoft.
