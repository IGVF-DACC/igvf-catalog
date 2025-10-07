FROM public.ecr.aws/nginx/nginx:1.29.1

RUN rm /etc/nginx/nginx.conf /etc/nginx/conf.d/default.conf

COPY ./production.conf /etc/nginx/nginx.conf
