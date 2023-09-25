import pypdf
import os
from langchain.document_loaders import PyPDFLoader
import typing as tp

from langchain.vectorstores import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    print("Please set OPENAI_API_KEY environment variable")
    exit()


class DBProvider:
    __db_faiss = None

    @staticmethod
    def get_db() -> FAISS:
        if DBProvider.__db_faiss is None:

            try:
                DBProvider.__db_faiss = FAISS.load_local("faiss_index", OpenAIEmbeddings())
            except:

                loader = PyPDFLoader("example_data/Clean_Architecture _Robert_Martin.pdf")
                pages = loader.load_and_split()

                DBProvider.__db_faiss = FAISS.from_documents(pages, OpenAIEmbeddings())

                DBProvider.__db_faiss.save_local("faiss_index")

        return DBProvider.__db_faiss


def main():
    db = DBProvider.get_db()

    docs = db.similarity_search("What is Liskov principle?", k=2)
    for doc in docs:
        print(str(doc.metadata["page"]) + ":", doc.page_content[:300])


if __name__ == "__main__":
    main()
