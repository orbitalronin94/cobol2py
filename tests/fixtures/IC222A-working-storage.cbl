      *HEADER,COBOL,IC222A                                                            
000100 IDENTIFICATION DIVISION.                                         IC2224.2
000200 PROGRAM-ID.                                                      IC2224.2
000300     IC222A.                                                      IC2224.2
000400****************************************************************  IC2224.2
000500*                                                              *  IC2224.2
000600*    VALIDATION FOR:-                                          *  IC2224.2
000700*                                                              *  IC2224.2
000800*    "ON-SITE VALIDATION, NATIONAL INSTITUTE OF STD & TECH.     ".IC2224.2
000900*                                                              *  IC2224.2
001000*    "COBOL 85 VERSION 4.2, Apr  1993 SSVG                      ".IC2224.2
001100*                                                              *  IC2224.2
001200****************************************************************  IC2224.2
001300*                                                              *  IC2224.2
001400*      X-CARDS USED BY THIS PROGRAM ARE :-                     *  IC2224.2
001500*                                                              *  IC2224.2
001600*            X-55   SYSTEM PRINTER                             *  IC2224.2
001700*            X-82   SOURCE-COMPUTER                            *  IC2224.2
001800*            X-83   OBJECT-COMPUTER.                           *  IC2224.2
001900*                                                              *  IC2224.2
002000****************************************************************  IC2224.2
002100*                                                              *  IC2224.2
002200*    THE SOURCE FILE CONTAINS TWO PROGRAMS, IC222A AND         *  IC2224.2
002300*    IC222A-1, WHICH TEST LANGUAGE ELEMENTS FROM  LEVEL 2 OF   *  IC2224.2
002400*    THE INTER-PROGRAM COMMUNICATION MODULE.  THE LANGUAGE     *  IC2224.2
002500*    ELEMENTS TESTED ARE:                                      *  IC2224.2
002600*          "ON EXCEPTION"     PHRASE                           *  IC2224.2
002700*          "NOT ON EXCEPTION" PHRASE                           *  IC2224.2
002800*          "END-CALL"         PHRASE                           *  IC2224.2
002900*          "ON OVERFLOW"      PHRASE                           *  IC2224.2
003000*                                                              *  IC2224.2
003100*    THE TWO PROGRAMS SHOULD BE COMPILED IN THE SAME           *  IC2224.2
003200*    INVOCATION OF THE COMPILER TO TEST THE BATCH COMPILATION  *  IC2224.2
003300*    FEATURE AND RECOGNITION OF THE END PROGRAM HEADER.  THE   *  IC2224.2
003400*    ARRANGEMENT OF THE PROGRAMS IN THE SOURCE FILE IS:        *  IC2224.2
003500*                                                              *  IC2224.2
003600*    IDENTIFICATION DIVISION.                                  *  IC2224.2
003700*    PROGRAM-ID. IC222A.                                       *  IC2224.2
003800*          .                                                   *  IC2224.2
003900*          .                                                   *  IC2224.2
004000*          .                                                   *  IC2224.2
004100*    END PROGRAM IC222A.                                          IC2224.2
004200*    IDENTIFICATION DIVISION.                                     IC2224.2
004300*    PROGRAM-ID. IC222A-1.                                        IC2224.2
004400*          .                                                   *  IC2224.2
004500*          .                                                   *  IC2224.2
004600*          .                                                   *  IC2224.2
004700*                                                              *  IC2224.2
004800*    IC222A, THE FIRST PROGRAM IN THE FILE, CONTAINS THE       *  IC2224.2
004900*    SUBSTANTIVE TESTS.  THE ONLY FUNCTION OF THE OTHER        *  IC2224.2
005000*    PROGRAM IS TO ENSURE THAT A PROGRAM WITH KNOWN PARAMETER  *  IC2224.2
005100*    REQUIREMENTS IS AVAILABLE TO BE CALLED.  IC222A TESTS     *  IC2224.2
005200*    CONTROL FLOW THROUGH VARIANTS OF THE CALL STATEMENT WITH  *  IC2224.2
005300*    THE "ON EXCEPTION" PHRASE PRESENT OR ABSENT; THE "NOT ON  *  IC2224.2
005400*    EXCEPTION" PHRASE PRESENT OR ABSENT; AND AVAILABLE OR     *  IC2224.2
005500*    NON-AVAIABLE TARGET PROGRAMS.  EACH CALL STATEMENT HAS AN *  IC2224.2
005600*    END-CALL PHRASE, AND THERE ARE SECONDARY TESTS WHICH      *  IC2224.2
005700*    CHECK THAT STATEMENTS FOLLOWING END-CALL ARE PROPERLY     *  IC2224.2
005800*    EXECUTED.                                                 *  IC2224.2
005900*                                                                 IC2224.2
006000*    THIS TEST SET DOES NOT EXAMINE THE RESULTS RETURNED BY    *  IC2224.2
006100*    THE CALLED PROGRAM, BUT IS WHOLLY CONCERNED WITH THE FLOW *  IC2224.2
006200*    OF CONTROL IN THE CALLING PROGRAM DURING EXECUTION OF A   *  IC2224.2
006300*    CALL STATEMENT.                                           *  IC2224.2
006400*                                                              *  IC2224.2
006500*    THERE ARE EIGHT POSIBLE COMBINATIONS OF CALL STATEMENT    *  IC2224.2
006600*    FORMAT AND CALLED PROGRAM AVAILABILITY THAT COULD BE      *  IC2224.2
006700*    TESTED.  TWO OF THESE COMBINATIONS, THOSE WHERE A PROGRAM *  IC2224.2
006800*    WHICH IS NOT AVAILABLE IS CALLED THROUGH  A STATEMENT     *  IC2224.2
006900*    WHICH DOES NOT CONTAIN AN "ON EXCEPTION" PHRASE, PRODUCE  *  IC2224.2
007000*    EFFECTS WHICH THE STANDARD LEAVES UNDEFINED.  THUS THERE  *  IC2224.2
007100*    ARE SIX CASES WHICH CAN BE TESTED.  THIS TEST SUITE TESTS *  IC2224.2
007200*    ALL SIX.  IN ADDITION, IT TESTS THE TWO CASES WHERE       *  IC2224.2
007300*    "ON OVERFLOW" CAN BE USED IN PLACE OF "ON EXCEPTION".     *  IC2224.2
007400*    EACH OF THE EIGHT MAJOR TESTS IS FOLLOWED BY A            *  IC2224.2
007500*    SUBORDINATE TEST WHICH IS INTENDED TO CHECK THE WAY       *  IC2224.2
007600*    THAT CONTROL HAS FLOWED THROUGH THE PHRASES OF THE CALL   *  IC2224.2
007700*    STATEMENT.  EVERY CALL STATEMENT IN IC222A HAS AN         *  IC2224.2
007800*    "END-CALL" SCOPE DELIMITER.  THIS SCOPE DELIMITER IS      *  IC2224.2
007900*    FOLLOWED BY ONE MORE STATEMENT IN THE SENTENCE, AND THE   *  IC2224.2
008000*    SUBORDINATE TESTS CHECK THAT THIS ADDITIONAL STATEMENT    *  IC2224.2
008100*    HAS BEEN EXECUTED.                                        *  IC2224.2
008200*                                                              *  IC2224.2
008300****************************************************************  IC2224.2
008400*                                                                 IC2224.2
008500 ENVIRONMENT DIVISION.                                            IC2224.2
008600 CONFIGURATION SECTION.                                           IC2224.2
008700 SOURCE-COMPUTER.                                                 IC2224.2
008800     XXXXX082.                                                    IC2224.2
008900 OBJECT-COMPUTER.                                                 IC2224.2
009000     XXXXX083.                                                    IC2224.2
009100 INPUT-OUTPUT SECTION.                                            IC2224.2
009200 FILE-CONTROL.                                                    IC2224.2
009300     SELECT PRINT-FILE ASSIGN TO                                  IC2224.2
009400     XXXXX055.                                                    IC2224.2
009500*                                                                 IC2224.2
009600 DATA DIVISION.                                                   IC2224.2
009700 FILE SECTION.                                                    IC2224.2
009800 FD  PRINT-FILE.                                                  IC2224.2
009900 01  PRINT-REC PICTURE X(120).                                    IC2224.2
010000 01  DUMMY-RECORD PICTURE X(120).                                 IC2224.2
010100*                                                                 IC2224.2
010200 WORKING-STORAGE SECTION.                                         IC2224.2
010300 77  DN1 PICTURE S99  VALUE ZERO.                                 IC2224.2
010400 77  DN3 PICTURE S99.                                             IC2224.2
010500 77  ID1 PICTURE X(8) VALUE "IC222A-1".                           IC2224.2
010600 77  ID2 PICTURE X(8).                                            IC2224.2
010700 77  DN2 PICTURE S99                                              IC2224.2
010800         USAGE COMPUTATIONAL, VALUE ZERO.                         IC2224.2
010900 77  DN4 PICTURE S99                                              IC2224.2
011000         USAGE IS COMPUTATIONAL.                                  IC2224.2
011100 77  CALL-FLAG PIC 9.                                             IC2224.2
011200 01  EXCEPTION-PATH-FLAG PICTURE X.                               IC2224.2
011300*                                                                 IC2224.2
011400 01  TEST-RESULTS.                                                IC2224.2
011500     02 FILLER                   PIC X      VALUE SPACE.          IC2224.2
011600     02 FEATURE                  PIC X(20)  VALUE SPACE.          IC2224.2
011700     02 FILLER                   PIC X      VALUE SPACE.          IC2224.2
011800     02 P-OR-F                   PIC X(5)   VALUE SPACE.          IC2224.2
011900     02 FILLER                   PIC X      VALUE SPACE.          IC2224.2
012000     02  PAR-NAME.                                                IC2224.2
012100       03 FILLER                 PIC X(19)  VALUE SPACE.          IC2224.2
012200       03  PARDOT-X              PIC X      VALUE SPACE.          IC2224.2
012300       03 DOTVALUE               PIC 99     VALUE ZERO.           IC2224.2
012400     02 FILLER                   PIC X(8)   VALUE SPACE.          IC2224.2
012500     02 RE-MARK                  PIC X(61).                       IC2224.2
012600 01  TEST-COMPUTED.                                               IC2224.2
012700     02 FILLER                   PIC X(30)  VALUE SPACE.          IC2224.2
012800     02 FILLER                   PIC X(17)  VALUE                 IC2224.2
012900            "       COMPUTED=".                                   IC2224.2
013000     02 COMPUTED-X.                                               IC2224.2
013100     03 COMPUTED-A               PIC X(20)  VALUE SPACE.          IC2224.2
013200     03 COMPUTED-N               REDEFINES COMPUTED-A             IC2224.2
013300                                 PIC -9(9).9(9).                  IC2224.2
013400     03 COMPUTED-0V18 REDEFINES COMPUTED-A   PIC -.9(18).         IC2224.2
013500     03 COMPUTED-4V14 REDEFINES COMPUTED-A   PIC -9(4).9(14).     IC2224.2
013600     03 COMPUTED-14V4 REDEFINES COMPUTED-A   PIC -9(14).9(4).     IC2224.2
013700     03       CM-18V0 REDEFINES COMPUTED-A.                       IC2224.2
013800         04 COMPUTED-18V0                    PIC -9(18).          IC2224.2
013900         04 FILLER                           PIC X.               IC2224.2
014000     03 FILLER PIC X(50) VALUE SPACE.                             IC2224.2
014100 01  TEST-CORRECT.                                                IC2224.2
014200     02 FILLER PIC X(30) VALUE SPACE.                             IC2224.2
014300     02 FILLER PIC X(17) VALUE "       CORRECT =".                IC2224.2
014400     02 CORRECT-X.                                                IC2224.2
014500     03 CORRECT-A                  PIC X(20) VALUE SPACE.         IC2224.2
014600     03 CORRECT-N    REDEFINES CORRECT-A     PIC -9(9).9(9).      IC2224.2
014700     03 CORRECT-0V18 REDEFINES CORRECT-A     PIC -.9(18).         IC2224.2
014800     03 CORRECT-4V14 REDEFINES CORRECT-A     PIC -9(4).9(14).     IC2224.2
014900     03 CORRECT-14V4 REDEFINES CORRECT-A     PIC -9(14).9(4).     IC2224.2
015000     03      CR-18V0 REDEFINES CORRECT-A.                         IC2224.2
015100         04 CORRECT-18V0                     PIC -9(18).          IC2224.2
015200         04 FILLER                           PIC X.               IC2224.2
015300     03 FILLER PIC X(2) VALUE SPACE.                              IC2224.2
015400     03 COR-ANSI-REFERENCE             PIC X(48) VALUE SPACE.     IC2224.2
015500 01  CCVS-C-1.                                                    IC2224.2
015600     02 FILLER  PIC IS X(99)    VALUE IS " FEATURE              PAIC2224.2
015700-    "SS  PARAGRAPH-NAME                                          IC2224.2
015800-    "       REMARKS".                                            IC2224.2
015900     02 FILLER                     PIC X(20)    VALUE SPACE.      IC2224.2
016000 01  CCVS-C-2.                                                    IC2224.2
016100     02 FILLER                     PIC X        VALUE SPACE.      IC2224.2
016200     02 FILLER                     PIC X(6)     VALUE "TESTED".   IC2224.2
016300     02 FILLER                     PIC X(15)    VALUE SPACE.      IC2224.2
016400     02 FILLER                     PIC X(4)     VALUE "FAIL".     IC2224.2
016500     02 FILLER                     PIC X(94)    VALUE SPACE.      IC2224.2
016600 01  REC-SKL-SUB                   PIC 9(2)     VALUE ZERO.       IC2224.2
016700 01  REC-CT                        PIC 99       VALUE ZERO.       IC2224.2
016800 01  DELETE-COUNTER                PIC 999      VALUE ZERO.       IC2224.2
016900 01  ERROR-COUNTER                 PIC 999      VALUE ZERO.       IC2224.2
017000 01  INSPECT-COUNTER               PIC 999      VALUE ZERO.       IC2224.2
017100 01  PASS-COUNTER                  PIC 999      VALUE ZERO.       IC2224.2
017200 01  TOTAL-ERROR                   PIC 999      VALUE ZERO.       IC2224.2
017300 01  ERROR-HOLD                    PIC 999      VALUE ZERO.       IC2224.2
017400 01  DUMMY-HOLD                    PIC X(120)   VALUE SPACE.      IC2224.2
017500 01  RECORD-COUNT                  PIC 9(5)     VALUE ZERO.       IC2224.2
017600 01  ANSI-REFERENCE                PIC X(48)    VALUE SPACES.     IC2224.2
017700 01  CCVS-H-1.                                                    IC2224.2
017800     02  FILLER                    PIC X(39)    VALUE SPACES.     IC2224.2
017900     02  FILLER                    PIC X(42)    VALUE             IC2224.2
018000     "OFFICIAL COBOL COMPILER VALIDATION SYSTEM".                 IC2224.2
018100     02  FILLER                    PIC X(39)    VALUE SPACES.     IC2224.2
018200 01  CCVS-H-2A.                                                   IC2224.2
018300   02  FILLER                        PIC X(40)  VALUE SPACE.      IC2224.2
018400   02  FILLER                        PIC X(7)   VALUE "CCVS85 ".  IC2224.2
018500   02  FILLER                        PIC XXXX   VALUE             IC2224.2
018600     "4.2 ".                                                      IC2224.2
018700   02  FILLER                        PIC X(28)  VALUE             IC2224.2
018800            " COPY - NOT FOR DISTRIBUTION".                       IC2224.2
018900   02  FILLER                        PIC X(41)  VALUE SPACE.      IC2224.2
019000                                                                  IC2224.2
019100 01  CCVS-H-2B.                                                   IC2224.2
019200   02  FILLER                        PIC X(15)  VALUE             IC2224.2
019300            "TEST RESULT OF ".                                    IC2224.2
019400   02  TEST-ID                       PIC X(9).                    IC2224.2
019500   02  FILLER                        PIC X(4)   VALUE             IC2224.2
019600            " IN ".                                               IC2224.2
019700   02  FILLER                        PIC X(12)  VALUE             IC2224.2
019800     " HIGH       ".                                              IC2224.2
019900   02  FILLER                        PIC X(22)  VALUE             IC2224.2
020000            " LEVEL VALIDATION FOR ".                             IC2224.2
020100   02  FILLER                        PIC X(58)  VALUE             IC2224.2
020200     "ON-SITE VALIDATION, NATIONAL INSTITUTE OF STD & TECH.     ".IC2224.2
020300 01  CCVS-H-3.                                                    IC2224.2
020400     02  FILLER                      PIC X(34)  VALUE             IC2224.2
020500            " FOR OFFICIAL USE ONLY    ".                         IC2224.2
020600     02  FILLER                      PIC X(58)  VALUE             IC2224.2
020700     "COBOL 85 VERSION 4.2, Apr  1993 SSVG                      ".IC2224.2
020800     02  FILLER                      PIC X(28)  VALUE             IC2224.2
020900            "  COPYRIGHT   1985,1986 ".                           IC2224.2
021000 01  CCVS-E-1.                                                    IC2224.2
021100     02 FILLER                       PIC X(52)  VALUE SPACE.      IC2224.2
021200     02 FILLER  PIC X(14) VALUE IS "END OF TEST-  ".              IC2224.2
021300     02 ID-AGAIN                     PIC X(9).                    IC2224.2
021400     02 FILLER                       PIC X(45)  VALUE SPACES.     IC2224.2
021500 01  CCVS-E-2.                                                    IC2224.2
021600     02  FILLER                      PIC X(31)  VALUE SPACE.      IC2224.2
021700     02  FILLER                      PIC X(21)  VALUE SPACE.      IC2224.2
021800     02 CCVS-E-2-2.                                               IC2224.2
021900         03 ERROR-TOTAL              PIC XXX    VALUE SPACE.      IC2224.2
022000         03 FILLER                   PIC X      VALUE SPACE.      IC2224.2
022100         03 ENDER-DESC               PIC X(44)  VALUE             IC2224.2
022200            "ERRORS ENCOUNTERED".                                 IC2224.2
022300 01  CCVS-E-3.                                                    IC2224.2
022400     02  FILLER                      PIC X(22)  VALUE             IC2224.2
022500            " FOR OFFICIAL USE ONLY".                             IC2224.2
022600     02  FILLER                      PIC X(12)  VALUE SPACE.      IC2224.2
022700     02  FILLER                      PIC X(58)  VALUE             IC2224.2
022800     "ON-SITE VALIDATION, NATIONAL INSTITUTE OF STD & TECH.     ".IC2224.2
022900     02  FILLER                      PIC X(8)   VALUE SPACE.      IC2224.2
023000     02  FILLER                      PIC X(20)  VALUE             IC2224.2
023100             " COPYRIGHT 1985,1986".                              IC2224.2
023200 01  CCVS-E-4.                                                    IC2224.2
023300     02 CCVS-E-4-1                   PIC XXX    VALUE SPACE.      IC2224.2
023400     02 FILLER                       PIC X(4)   VALUE " OF ".     IC2224.2
023500     02 CCVS-E-4-2                   PIC XXX    VALUE SPACE.      IC2224.2
023600     02 FILLER                       PIC X(40)  VALUE             IC2224.2
023700      "  TESTS WERE EXECUTED SUCCESSFULLY".                       IC2224.2
023800 01  XXINFO.                                                      IC2224.2
023900     02 FILLER                       PIC X(19)  VALUE             IC2224.2
024000            "*** INFORMATION ***".                                IC2224.2
024100     02 INFO-TEXT.                                                IC2224.2
024200       04 FILLER                     PIC X(8)   VALUE SPACE.      IC2224.2
024300       04 XXCOMPUTED                 PIC X(20).                   IC2224.2
024400       04 FILLER                     PIC X(5)   VALUE SPACE.      IC2224.2
024500       04 XXCORRECT                  PIC X(20).                   IC2224.2
024600     02 INF-ANSI-REFERENCE           PIC X(48).                   IC2224.2
024700 01  HYPHEN-LINE.                                                 IC2224.2
024800     02 FILLER  PIC IS X VALUE IS SPACE.                          IC2224.2
024900     02 FILLER  PIC IS X(65)    VALUE IS "************************IC2224.2
025000-    "*****************************************".                 IC2224.2
025100     02 FILLER  PIC IS X(54)    VALUE IS "************************IC2224.2
025200-    "******************************".                            IC2224.2
025300 01  CCVS-PGM-ID                     PIC X(9)   VALUE             IC2224.2
025400     "IC222A".                                                    IC2224.2
025500*                                                                 IC2224.2
025600 PROCEDURE DIVISION.
025700 MAIN.
025800     MOVE SPACE TO TEST-RESULTS.
025900     MOVE "PASS " TO FEATURE OF TEST-RESULTS.
026000     DISPLAY FEATURE OF TEST-RESULTS.
026100     STOP RUN.
