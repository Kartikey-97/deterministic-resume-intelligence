import os
from ingestion.extractor import extract_text, extract_fitz, extract_pdfplumber

SAMPLE_FOLDER= "data/sample"

def test_extraction():
  

  files = os.listdir(SAMPLE_FOLDER)[:1] # this only gets the first one files

  for file in files:
    path=os.path.join(SAMPLE_FOLDER,file)

    print("="*50)
    print("Testing",file)

    try:
        text=extract_text(path)

        text1=extract_pdfplumber(path)
        text2=extract_fitz(path)

        if len(text.strip())<500:
            print("this was a weak extraction")
        
        
        print("\n This is the extracted text: \n")
        #print("\n First 500 characters: \n")
        print()
        print()

        print("="*50)
        print("\n This is the normal extracted text: \n")
        print("Extracted length: ", len(text))
        print(text)
        print()
        print()

        print("="*50)
        print("\n This is the pdfplumber text: \n")
        print("Extracted length: ", len(text1))
        print(text1)
        print()
        print()

        print("="*50)
        print("\n This is the fitz text: \n")
        print("Extracted length: ", len(text2))
        print(text2)
        print()
        print()

        print("="*50)
        print("Difference between fitz and pdfplumber:")
        print(len(set(text1.split()) - set(text2.split())))
                    

    except Exception as e:
       print("Failed cause of : ",e)


if __name__=="__main__":
   test_extraction()


    
  