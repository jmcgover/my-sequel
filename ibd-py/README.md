# IBD Tools (Python)

## Extracting Parsable Info

```bash
time seq 201 832 | parallel '-j60' \
  poetry run uv run src/read.py \
    -f ~/Downloads/backup/trunks/mariadb/var/lib/mysql/MyVideos116/files.ibd \
    --schema ./schema_files.yaml \
    --page {} \
    --outfile files.csv
```

## Displaying All CSVs
```bash
cat files*.csv | xan sort --select strFilename | xan view --color=always --all | less -SR
```

## Querying SQLite Database
```sql
SELECT t.c00 as 'Show Name',f.*,c.* FROM tvshow t, tvshowcounts c, tvshowlinkpath l, files f WHERE c.idShow == t.idShow AND l.idShow == t.idShow AND l.idPath == f.idPath AND c.watchedcount > 0;
```
