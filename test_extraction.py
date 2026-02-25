import os
from ingestion.extractor import extract_text, extract_fitz, extract_pdfplumber
from utils.text_cleaner import clean_text
from segmentation.section_detector import segment_resume

SAMPLE_FOLDER= "data/sample"



def single_extraction():
    files2="data/sample/Resume-Sample-2.pdf"
    print("="*50)
    print("Testing",files2)

    try:
        text=extract_fitz(files2)

        text1=clean_text(extract_pdfplumber(files2))

        text2=clean_text(extract_fitz(files2))

        text3=extract_pdfplumber(files2)

        if len(text.strip())<500:
            print("this was a weak extraction")
        
        
        print("\n This is the extracted text: \n")
        #print("\n First 500 characters: \n")
        print()
        print()

        print("="*50)
        print("\n This is the cleaned extracted fitz text: \n")
        clean_text(text)
        print("Extracted length: ", len(text))
        print(text)


        sections = segment_resume(text2)

        print(sections["skills"]["lines"])
        print(sections["skills"]["confidence"])
        print("\nDetected sections and confidence:\n")
        for k, v in sections.items():
            print(k, "->", v["confidence"])
            print("Sample:", v["lines"][:2])
            print()
        print()
        print()

        
        """
        print("="*50)
        print("\n This is the unlcleaned fitz text: \n")
        print("Extracted length: ", len(text2))
        print(text2)
        print()
        print()


        print("="*50)
        print("\n This is the cleaned pdfplumber text: \n")
        print("Extracted length: ", len(text1))
        print(text1)
        print()
        print()

        print("="*50)
        print("\n This is the uncleaned pdfplumber text: \n")
        print("Extracted length: ", len(text3))
        print(text3)
        print()
        print()

        

        print("="*50)
        print("Difference between fitz and pdfplumber:")
        print(len(set(text1.split()) - set(text2.split())))
        """          

    except Exception as e:
       print("Failed cause of : ",e)


    
def test_extraction():

  files = os.listdir(SAMPLE_FOLDER)[:2] # this only gets the first one files

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
   single_extraction()



    
  