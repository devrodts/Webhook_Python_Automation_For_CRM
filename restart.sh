#!/bin/bash


sudo systemctl daemon-reload 
sudo systemctl restart commel_automacoes.service
sudo systemctl enable commel_automacoes.service 


