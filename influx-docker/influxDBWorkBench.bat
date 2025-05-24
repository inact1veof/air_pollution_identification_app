@ECHO OFF

SET JAVA_EXE="java.exe"
SET JAVA_OPTS="-Dfile.encoding=utf-8"
SET ASTRA="\Users\user\DockerProjects\influx-docker\influxDBWorkBench.jar"

%JAVA_EXE% %JAVA_OPTS% -jar %ASTRA%

@ECHO ON
