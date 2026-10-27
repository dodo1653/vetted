# garlic launch film (35 s, 1080p30)

`out/garlic-launch-35s.mp4`. Topic: the vamp problem and how garlic solves it. Every coin, number and image is real,
recorded from garlic's relay on 27 Oct 2026 (~19:10-20:45 UTC) and from the chain.

## Sources
- `data/board.json`: the relay's board at recording time (`/v1/board`): 541 copies caught in the last hour,
  953 since the relay started (~1.7 h), 1,397 launches in its 65-minute window.
- `data/c_<mint>.json`: `/v1/coin` for every original with copies (the copies lists).
- `data/story.json`: the two cases in the film, with each copy's own data:
  - **$TOLANA**: original 9KaDUUXW… (41 buyers); copy Czcsbh4r… launched 2 min later reached 170 buyers.
    That copy's art is hosted on gmgn.ai, which blocks downloads, so the film shows the site's ticker tile for it (as the site does).
  - **$RATIOED**: original DhfeVpo1… (28 buyers); copies +0 min (26 buyers), +1 min (18), +13 min (3).
    The first two use the byte-identical image file (same SHA-256) and the same description.
- `img/`: the coins' own images (pump.fun IPFS via pump.mypinata.cloud / gateway.pinata.cloud; copy metadata URIs read
  from the Token-2022 mint's metadata extension).
- `data/film.js`: what the film draws, assembled from the files above.
- `../brand/garlic_coin.png`: the coin render (`../brand/garlic.py`).

## Scenes
0-9.9 TOLANA (the copy outruns the original) · 9.9-14.6 RATIOED (same ticker, name, picture) · 14.6-18.8 "541 copies in one
hour" · 18.8-23 garlic, "no more vamps." · 23-29.4 the board: counters, copies marked COPY, hidden · 29.4-32.6 the create
form refusing $TOLANA · 32.6-35 end card ($GARLIC, @garlicdeploys).

## Re-render
Serve `D:\cooks\vetted` on 8799 (`python -m http.server 8799`), then:
```
DUR=35 node music.mjs out/music.wav
cd /d/cooks/pitwall && bash render_film.sh "http://127.0.0.1:8799/promo/film.html" /d/cooks/vetted/promo/frames120 35 /d/cooks/vetted/promo/out/music.wav /d/cooks/vetted/promo/out/garlic-launch-35s.mp4
```
Stills: `node /d/cooks/pitwall/render.mjs <url> <dir> 30 0 0 "3.6,8.6,13.6"`.
