       IDENTIFICATION DIVISION.
       PROGRAM-ID. B042.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 WS-A PIC 9 VALUE 2.
       01 WS-B PIC 9 VALUE 0.
       PROCEDURE DIVISION.
       MAIN-PARA.
           IF WS-A = 2 OR WS-B = 3
               DISPLAY "EITHER"
           ELSE
               DISPLAY "OTHER"
           END-IF.
           STOP RUN.
