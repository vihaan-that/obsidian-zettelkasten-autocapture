---
tags: [dashboard]
---

# Research Log Dashboard

## Recent Daily Logs
```dataview
TABLE contributor, summary, status, file.ctime AS captured
FROM "50-Daily-Logs"
SORT file.ctime DESC
LIMIT 10
```

## Recent Journals
```dataview
TABLE contributor, tags, file.ctime AS captured
FROM "55-Journals"
SORT file.ctime DESC
LIMIT 10
```

## Open Experiments
```dataview
TABLE contributor, status, summary
FROM "40-Experiments"
WHERE status != "done" AND status != "completed"
SORT file.ctime DESC
```

## Team Activity (Last 7 Days)
```dataview
TABLE type, summary, file.ctime AS when
FROM "50-Daily-Logs" OR "55-Journals" OR "40-Experiments"
WHERE file.ctime >= date(today) - dur(7 days)
SORT file.ctime DESC
```

## By Contributor
```dataview
TABLE WITHOUT ID
  contributor AS "Who",
  length(rows) AS "Entries",
  max(rows.file.ctime) AS "Last Active"
FROM "50-Daily-Logs" OR "55-Journals" OR "40-Experiments"
GROUP BY contributor
SORT length(rows) DESC
```

---

## Recent Code Sessions
```dataview
TABLE repo, branch, summary
FROM "20-Code-Sessions"
SORT file.ctime DESC
LIMIT 8
```

## Recent Research
```dataview
TABLE contributor, summary, tags
FROM "30-Research"
SORT file.ctime DESC
LIMIT 8
```

## Recent LLM Chats
```dataview
TABLE summary, file.ctime AS captured
FROM "10-LLM-Chats"
SORT file.ctime DESC
LIMIT 8
```
