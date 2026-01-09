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

## Showing the Data Distribution

Based on [The basics of InnoDB space file layout](https://blog.jcole.us/2013/01/03/the-basics-of-innodb-space-file-layout/) explainign that the page size is 16384 bytes and using a file-binary visualizer, [bin-graph](https://github.com/jmcgover/bin-graph), we can see that large swaths of the `.idb` file are empty for a given tablespace in order to leave room for the table to grow.

As a result, many of the records will not be parsable or will parse empty. Given that the tablespace in question is 13631488 bytes, we should expect $13631488  / 16384 = 832$ pages total, many of which are empty past the halfway point, based on the visualization of data distribution:

![Binary data sitribution of files.ibd 16384 pixels wide in 'ascii' mode: The color of each pixel represents the "printability" of each sample in a linear way. Black represents a null byte (00), white represents a set byte (FF), blue represents printable characters and red represents any other value.](assets/files-ascii-w16384.png)

In the above image, each line represents a page and the color of each pixel represents the "printability" of each sample in a linear way: black represents a null byte (00), white represents a set byte (FF), blue represents printable characters and red represents any other value.
