FROM python:3.10-bullseye

RUN apt-get update && \
        apt-get -y install -y \
        openjdk-11-jdk 
# Install R
RUN apt-get update && apt-get install -y r-base

# get jenkins
RUN set -eux; \
        mkdir /home/jenkins/; \
        wget -O /home/jenkins/jenkins.jar https://get.jenkins.io/war-stable/2.414.3/jenkins.war; \
        chmod -R 770 /home/jenkins

# Install Apache Spark
ENV APACHE_SPARK_VERSION 3.2.1
ENV HADOOP_VERSION 3.2
ENV SPARK_HOME /spark

RUN apt-get install -y curl && \
    curl -sL --retry 3 "https://archive.apache.org/dist/spark/spark-$APACHE_SPARK_VERSION/spark-$APACHE_SPARK_VERSION-bin-hadoop$HADOOP_VERSION.tgz" | \
    tar -xz -C /opt && \
    mv /opt/spark-$APACHE_SPARK_VERSION-bin-hadoop$HADOOP_VERSION $SPARK_HOME && \
    rm -rf /opt/*

# Set environment variables
ENV PATH $PATH:$SPARK_HOME/bin
ENV PYTHONPATH $SPARK_HOME/python:$PYTHONPATH
ENV PYSPARK_PYTHON python

# Install necessary R packages (replace these with your required packages)
# move jenkins configurations
COPY --chmod=770 --from=assets_jenkins . /home/.jenkins/

# move all R scripts to Container
COPY --chmod=770 ./Scripts/R/* /opt/apps/batched/R/
COPY --chmod=770 ./Scripts/Python/* /opt/apps/batched/Python/

# install all R packages
# RUN R -e 'packToInst <- read.csv("/opt/apps/batched/R/requirements.txt"); lapply(packToInst$Packages, function(x) install.packages(x))'
RUN python -m pip install poetry
CMD pip3 -v
