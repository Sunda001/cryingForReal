FROM arata74/mirrorclone
WORKDIR /usr/src/app
RUN chmod 777 /usr/src/app
COPY lmao.txt .
RUN pip3 install --no-cache-dir -r lmao.txt
COPY . .
CMD ["bash", "start.sh"]
