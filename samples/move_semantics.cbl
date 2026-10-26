       IDENTIFICATION DIVISION.
       PROGRAM-ID. MOVESEMANTICS.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 WS-CODE PIC X(5).
       01 WS-NUM  PIC 9(3).
       PROCEDURE DIVISION.
       MAIN.
           MOVE "ABCDEFG" TO WS-CODE.
           DISPLAY "[" WS-CODE "]".
           MOVE 1234 TO WS-NUM.
           DISPLAY WS-NUM.
           MOVE "A" TO WS-CODE.
           DISPLAY "[" WS-CODE "]".
           STOP RUN.
