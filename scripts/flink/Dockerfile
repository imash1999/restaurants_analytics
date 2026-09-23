FROM flink:1.17-java11

COPY lib/*.jar /opt/flink/lib/

COPY submit.sql /opt/flink/submit.sql

CMD ["/opt/flink/bin/sql-client.sh", "-f", "/opt/flink/submit.sql"]
