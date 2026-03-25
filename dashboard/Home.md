---
tags: [dashboard]
---

# 🧠 Knowledge Dashboard

## Recent LLM Chats
```dataview
TABLE summary, file.ctime AS captured
FROM "10-LLM-Chats"
SORT file.ctime DESC
LIMIT 8
```

## Recent Code Sessions
```dataview
TABLE repo, branch, summary
FROM "20-Code-Sessions"
SORT file.ctime DESC
LIMIT 8
```

## Recent Research
```dataview
TABLE summary, tags
FROM "30-Research"
SORT file.ctime DESC
LIMIT 8
```

## Open Experiments
```dataview
TABLE hypothesis, status
FROM "40-Experiments"
WHERE status != "done"
SORT file.ctime DESC
```
