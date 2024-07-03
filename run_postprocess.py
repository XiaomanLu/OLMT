from model_ELM import ELMcase
import pickle, os

case = '20240613_US-UMB_ICBELMBC'

#Load case object
myfile=open('./pklfiles/'+case+'.pkl','rb')
mycase=pickle.load(myfile)

process_vars=['FPSN','FSH','EFLX_LH_TOT','QRUNOFF','QSOIL','QVEGE','QVEGT','SNOWDP', \
        'ZWT','TLAI']

for v in process_vars:
  mycase.postprocess(v, startyear=1990,endyear=2009,dailytomonthly=True)
mycase.create_pkl()
