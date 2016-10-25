Install filebeat according to docs:
(https://www.elastic.co/guide/en/beats/filebeat/current/filebeat-getting-started.html)

Generate SSL keys for lumberjack
Use with each beat deployment

test with 
`curl -XGET 'http://localhost:9200/filebeat-*/_search?pretty'`