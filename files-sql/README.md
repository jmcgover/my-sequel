# Fixing the `files` Table

## Querying SQLite Database
```sql
SELECT t.c00 as 'Show Name',f.*,c.* FROM tvshow t, tvshowcounts c, tvshowlinkpath l, files f WHERE c.idShow == t.idShow AND l.idShow == t.idShow AND l.idPath == f.idPath AND c.watchedcount > 0;
```

```bash
just run --database ~/Downloads/backup/toots/home/dumbo/MyVideos131.db --csv ~/Downloads/backup/trunks/mariadb/csv/files.csv | pbcopy
```

