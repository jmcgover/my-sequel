# IBD Tools (Python)

```bash
time seq 201 832 | parallel '-j60' \
  poetry run uv run src/read.py \
    -f ~/Downloads/backup/trunks/mariadb/var/lib/mysql/MyVideos116/files.ibd \
    --schema ./schema_files.yaml \
    --page {} \
    --outfile files.csv
```

```bash
cat files*.csv | xan sort --select strFilename | xan view --color=always | less -SR
```
