import os
from tkinter import *

window=Tk()
window.title('Sortinator')



def renamefiles():
    filespath=direntry.get()
    #проверяем есть ли папка
    if os.path.isdir(filespath)==True:
        #получаем список с именами и датами
        files=os.listdir(filespath)
        fileswithdates=[(file, os.path.getmtime(os.path.join(filespath, file))) for file in files]
        sortedfiles=sorted(fileswithdates, key=lambda x: x[1])
        #проверяем надо ли добавлять нули
        if addzeros.get()==1:
            for i in range(len(sortedfiles)):
                #номер файла
                filenumber=i
                if firstnumber.get()==1:
                    filenumber=filenumber+1
                #получаем расширение файла
                file_name,file_extension=os.path.splitext(sortedfiles[i][0])
                #проверяем сколько надо добавить нулей
                if filenumber<100:
                    if filenumber<10:
                        os.rename(os.path.join(filespath,sortedfiles[i][0]),os.path.join(filespath,'00'+str(filenumber)+file_extension))
                    else:
                        os.rename(os.path.join(filespath,sortedfiles[i][0]),os.path.join(filespath,'0'+str(filenumber)+file_extension))
                else:
                    os.rename(os.path.join(filespath,sortedfiles[i][0]),os.path.join(filespath,str(filenumber)+file_extension))
        else:
            for i in range(len(sortedfiles)):
                #номер файла
                filenumber=i
                if firstnumber.get()==1:
                    filenumber=filenumber+1
                #получаем расширение файла
                file_name,file_extension=os.path.splitext(sortedfiles[i][0])
                os.rename(os.path.join(filespath,sortedfiles[i][0]),os.path.join(filespath,str(filenumber)+file_extension))
    else:
        outputlabel.configure(text='Directory does not exist')



dirlabel=Label(window,text='Select directory')
dirlabel.grid(column=1,row=0)

direntry=Entry(window,width=30)
direntry.grid(column=1,row=1)

firstnumberlabel=Label(window,text='First number')
firstnumberlabel.grid(column=1,row=2)

firstnumber=IntVar()

zerofirstselect=Radiobutton(window,text='0',value=0,variable=firstnumber)
zerofirstselect.grid(column=1,row=3)

onefirstselect=Radiobutton(window,text='1',value=1,variable=firstnumber)
onefirstselect.grid(column=1,row=4)

addzeroslabel=Label(window,text='Add zeros')
addzeroslabel.grid(column=1,row=5)

addzeros=IntVar()

nozeros=Radiobutton(window,text='1-2-3',value=0,variable=addzeros)
nozeros.grid(column=1,row=6)

yeszeros=Radiobutton(window,text='001-002-003',value=1,variable=addzeros)
yeszeros.grid(column=1,row=7)

renamebutton=Button(window,text='Rename',command=renamefiles)
renamebutton.grid(column=1,row=8)

outputlabel=Label(window,text='')
outputlabel.grid(column=1,row=9)

window.mainloop()
