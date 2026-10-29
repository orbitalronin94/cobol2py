       IDENTIFICATION DIVISION.
       PROGRAM-ID. MOVESEMANTICS.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 WS-CODE PIC X(5).
       01 WS-NUM  PIC 9(3).
       01 WS-BLANK PIC X(3).
       01 WS-INITIAL PIC X(5) VALUE "A".
       PROCEDURE DIVISION.
       MAIN.
           DISPLAY "[" WS-BLANK "]".
           DISPLAY "[" WS-INITIAL "]".
           MOVE "ABCDEFG" TO WS-CODE.
           DISPLAY "[" WS-CODE "]".
           MOVE 1234 TO WS-NUM.
           DISPLAY WS-NUM.
           MOVE "A" TO WS-CODE.
           DISPLAY "[" WS-CODE "]".
           STOP RUN.
