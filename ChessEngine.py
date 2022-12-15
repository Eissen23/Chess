"""
This class is responsible for storing all the information about the current state of a chess game. It will also be 
responsible for determining the valid moves at the current state. It will also keep a move log.
"""

class GameState():
    def __init__(self):
        #board is an 8x8 2d list, each element of the list has 2 characters.
        #1st character = piece color, 'b' or 'w'
        #2nd character = type of piece, 'K', 'Q', 'R', 'B', 'N' or 'P'
        #"--" = empty space
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]]
        self.moveFunctions = {'p': self.getPawnMoves, 'R': self.getRookMoves, 'N': self.getKnightMoves,
                              'B': self.getBishopMoves, 'Q': self.getQueenMoves, 'K': self.getKingMoves}
        
        self.whiteToMove = True
        self.movelog = []
        self.whiteKingLocation = (7, 4)
        self.blackKingLocation = (0, 4)
        self.inCheck = False
        self.pins = []
        self.checks = []
        self.checkmate = False
        self.stalemate = False
        self.enPassantPossible = () #coordinates for the square where en passant capture is possible
        self.enPassantPossibleLog = [self.enPassantPossible]
        #castling rights
        self.currentCastlingRight = CastleRights(True, True, True, True)
        self.castleRightsLog = [CastleRights(self.currentCastlingRight.wks, self.currentCastlingRight.bks,
                                             self.currentCastlingRight.wqs, self.currentCastlingRight.bqs)]
         

    """
    Make the move that is passed as a parameter
    """
    def makeMove(self, move):
        self.board[move.endRow][move.endCol] = move.pieceMoved
        self.board[move.startRow][move.startCol] = "--"
        self.movelog.append(move) #log move
        self.whiteToMove = not self.whiteToMove #switch turns
        
        #update the king's position
        if move.pieceMoved == 'wK':
            self.whiteKingLocation = (move.endRow, move.endCol)
        elif move.pieceMoved == 'bK':
            self.blackKingLocation = (move.endRow, move.endCol)     
        
        #if pawn moves twice, next move can capture enpassant
        if move.pieceMoved[1] == 'p' and abs(move.startRow - move.endRow) == 2:
            self.enPassantPossible = ((move.endRow + move.startRow)//2, move.endCol)
        else:
            self.enPassantPossible = ()
        
        #if enpassant move, must update the board to capture the pawn
        if move.enPassant:
            self.board[move.startRow][move.endCol] = "--" #capturing the pawn
        
        #if pawn promotion change piece
        if move.pawnPromotion:
            promotedPiece = input("Promote to Q, R, B, or N:") #we can make this part of the ui later
            self.board[move.endRow][move.endCol] = move.pieceMoved[0] + promotedPiece       
                
        # castle moves
        if move.castle:
            if move.endCol - move.startCol == 2: #kingside
                self.board[move.endRow][move.endCol - 1] = self.board[move.endRow][move.endCol + 1] #move rook
                self.board[move.endRow][move.endCol + 1] = '--' #emtpy space where rook was
            else: #queenside
                self.board[move.endRow][move.endCol + 1] = self.board[move.endRow][move.endCol - 2] #move rook
                self.board[move.endRow][move.endCol - 2] = '--' #emtpy space where rook was       
        
        self.enPassantPossibleLog.append(self.enPassantPossible)
                  
        #update castling rights
        self.updateCastleRights(move)
        self.castleRightsLog.append(CastleRights(self.whiteCastleKingside.wks, self.blackCastleKingside.bks,
                                                 self.whiteCastleQueenside.wqs, self.blackCastleQueenside.bqs))

    """
    Undo the last move made
    """
    def undoMovve(self):
        if len(self.movelog) != 0: #make sure that there is a move to undo
            move = self.movelog.pop()
            self.board[move.startRow][move.startCol] = move.pieceMoved #put piece on starting square
            self.board[move.endRow][move.endCol] = move.pieceCaptured #put back captured piece
            self.whiteToMove = not self.whiteToMove #switch turn backs
         
            #update the king's position 
            if move.pieceMoved == 'wK':
                self.whiteKingLocation = (move.startRow, move.startCol)
            elif move.pieceMoved == 'bK':
                self.blackKingLocation = (move.startRow, move.startCol)
            
            #undo enpassant is different
            if move.enPassant:
                self.board[move.endRow][move.endCol] = '--' #removes the pawn that was added in the wrong square
                self.board[move.startRow][move.endCol] = move.pieceCapture #puts the pawn back on the correct square it was captured from
             
            self.enPassantPossibleLog.pop()
            self.enPassantPossible = self.enPassantPossibleLog[-1]

            #undo a 2 square pawn advance
            if move.pieceMoved[1] == 'p' and abs (move.startRow - move.endRow) == 2:
                self.enPassantPossible = ()

            #update castling rights - whenever it is a rook or a king move    
            self.enPassantPossibleLog.pop()
            self.enPassantPossible = self.enPassantPossibleLog[-1]
                       
            #give back castle rights if move took them away
            self.castleRightsLog.pop() #get rid of the new castle rights from the move are undoing
            newRights = self.castleRightsLog[-1]
            self.currentCastlingRight = CastleRights(newRights.wks, newRights.bks, newRights.wqs, newRights.bqs) #set the current castle rights to the last one in the list

            #undo castle move
            if move.castle:
                if move.endCol - move.startCol == 2: #kingside
                    self.board[move.endRow][move.endCol + 1] = self.board[move.endRow][move.endCol - 1] #move rook
                    self.board[move.endRow][move.endCol - 1] = '--' #emtpy space where rook was
                else: #queenside
                    self.board[move.endRow][move.endCol - 2] = self.board[move.endRow][move.endCol + 1] #move rook
                    self.board[move.endRow][move.endCol + 1] = '--' #emtpy space where rook was

            self.checkmate = False;
            self.stalemate = False;

    """
    All moves with considering checks
    """
    def getValidMoves(self):
        for log in self.castleRightsLog:
            print(log.wks, log.wqs, log.bks, log.bqs, end=", ")
        print()
        tempEmpassantPossible = self.enPassantPossible
        tempCastleRights = CastleRights(self.currentCastlingRight.wks, self.currentCastlingRight.bks,
                                             self.currentCastlingRight.wqs, self.currentCastlingRight.bqs)
        #1.) generate all possible moves
        moves = self.getAllPossibleMoves()
        self.inCheck, self.pins, self.checks = self.checkForPinsAndChecks()
        if self.whiteToMove:
            kingRow = self.whiteKingLocation[0]
            kingCol = self.whiteKingLocation[1]
            self.getCastleMoves(self.whiteKingLocation[0], self.whiteKingLocation[1], moves)
        else:
            kingRow = self.blackKingLocation[0]
            kingCol = self.blackKingLocation[1]
            self.getCastleMoves(self.blackKingLocation[0], self.blackKingLocation[1], moves)
        #2.) for each move, make the move
        for i in range(len(moves) - 1, -1, -1): #when removing a list go backwards throught that list
            self.makeMove(moves[i])
            #3.) generate all the opponent's moves
            #4.) for each of your opponent's move, see if they ataack your king
            self.whiteToMove = not self.whiteToMove
            if self.inCheck():
                moves.remove(moves[i]) #5.) if they do attacck your king, not a valid move
            self.whiteToMove = not self.whiteToMove
            self.undoMove()       

        if self.inCheck:
            if len(self.checks) == 1: #only 1 check, block check or move king
                moves = self.getAllPossibleMoves()
                #to block a check you must move a piece into one of the squares between the enemy piece and king
                check = self.checks[0] #check information
                checkRow = check[0]
                checkCol = check[1]
                pieceChecking = self.board[checkRow][checkCol] #enemy piece causing the check
                validSquares = [] #squares that pieces can move to
                #if knight, must capture knight or move king, other pieces can be blocked
                if pieceChecking[1] == 'N':
                    validSquares = [(checkRow, checkCol)]
                else:
                    for i in range(1, 8):
                        validSquare = (kingRow + check [2] * i, kingCol + check[3] * i) #check[2] and check[3] are the check directions
                        validSquare.append(validSquare)
                        if validSquare[0] == checkRow and validSquare[1] == checkCol: #once you get piece and checks
                            break
                #get rid of any moves that don't block check or move king
                for i in range(len(moves) - 1, -1, -1): #go through backwards when you are removing from a list as iterating
                    if moves[i].pieceMoved[1] != 'K': #move doesn't move king so it must block or capture
                        if not (moves[i].endRow, moves[i].endCol) in validSquares: #move doesn't block check or capture piece
                            moves.remove(moves[i])
            else: #double check, king has to move
                self.getKingMoves(kingRow, kingCol, moves)
        else: #not in check so all moves are fine
            moves = self.getAllPossibleMoves()

        if len(moves) == 0:
            if self.inCheck:
                self.checkmate = True
            else:
                self.stalemate = True
        else:
            self.checkmate = False
            self.stalemate = False
               
        self.enPassantPossible = tempEmpassantPossible
        self.currentCastlingRight = tempCastleRights
            
        return moves
    
    """
    All moves with without considering checks
    """
    def getAllPossibleMoves(self):
        moves = []
        for r in range(len(self.board)):
            for c in range(len(self.board[r])):
                turn = self.board[r][c][0]
                if (turn == 'w' and self.whiteToMove) or (turn == 'b' and not self.whiteToMove):
                    piece = self.board[r][c][1]
                    self.moveFunctions[piece](r, c, moves) #calls the appropriate move function based on piece type
        return moves
  
    """
    Determine if the current player is in check
    """
    def inCheck(self):
        if self.whiteToMove:
            return self.squareUnderAttack(self.whiteKingLocation[0], self.whiteKingLocation[1])
        else:
            return self.squareUnderAttack(self.blackKingLocation[0], self.blackKingLocation[1])
    
    """
    Determine if the enemy can attack the square r, c
    """
    def squareUnderAttack(self, r, c):
        self.whiteToMove = not self.whiteToMove #switch to opponent's turn
        oppMoves = self.getAllPossibleMoves()
        self.whiteToMove = not self.whiteToMove #switch turn backs
        for move in oppMoves:
            if move.endRow == r and move.endCol == c: #square is under attack
                return True
        return False

    """
    Get pawn moves given starting row and column, append the new moves to the list 'moves'
    """
    def getPawnMoves(self, r, c, moves):
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])           
                self.pins.remove(self.pins[i])
                break

        if self.whiteToMove:
            moveAmount = -1
            startRow = 6
            backRow = 0
            kingRow, kingCol = self.whiteKingLocation
            enemyColor = 'b'
        else:
            moveAmount = 1
            startRow = 1 
            backRow = 7
            kingRow, kingCol = self.blackKingLocation
            enemyColor = 'w'
        
        pawnPromotion = False

        if self.board[r + moveAmount][c] == "--": #1 square moves
            if not piecePinned or pinDirection == (moveAmount, 0):
                if r + moveAmount == backRow: #if piece gets to bank rank then it is a pawn promotion
                    pawnPromotion = True
                moves.append(Move((r, c), (r + moveAmount, c), self.board, pawnPromotion = pawnPromotion))
                if r == startRow and self.board[r + 2 * moveAmount][c] == "--": #2 square moves
                    moves.append(Move((r, c), (r + 2 * moveAmount, c), self.board))
            #captures
            if c-1 >= 0: #captures to the left       
                if not piecePinned or pinDirection == (moveAmount, -1):
                    if self.board[r + moveAmount][c - 1][0] == enemyColor : #enemy piece to capture 
                       if r + moveAmount == backRow: #if piece gest to bank rank then it is pawn promotion
                            pawnPromotion = True
                       moves.append(Move((r, c), (r + moveAmount, c - 1), self.board, pawnPromotion = pawnPromotion))
                if (r + moveAmount, c - 1) == self.enPassantPossible:
                     attackingPiece = blockingPiece = False
                     if kingRow == r:
                         if kingCol < c: #king is the left of the pawn
                             #inside between king and pawn; outside range between pawn border
                             insideRange = range(kingCol + 1, c - 1)
                             outsideRange = range(c + 1, 8)
                         else: #king is the right of the pawn
                             insideRange = range(kingCol - 1, c, - 1)
                             outsideRange = range(c - 2, -1, -1)
                             for i in insideRange:
                                 if self.board[r][i] != "--": #some other piece beside en-passant pawn blocks
                                    blockingPiece = True
                             for i in outsideRange:
                                 square = self.board[r][i]
                                 if square[0] == enemyColor and (square[1] == "R" or square[1] == "Q"): #attacking
                                    attackingPiece = True
                                 elif square!= "--":
                                    blockingPiece = True
                     if not attackingPiece or blockingPiece:
                         moves.append(Move((r, c), (r + moveAmount, c - 1), self.board, enPassant = True))                    
            if c+1 <= 7: #captures to the right             
                if not piecePinned or pinDirection == (moveAmount, 1):
                    if self.board[r + moveAmount][c + 1][0] == enemyColor : #enemy piece to capture                     
                        pawnPromotion = True
                    moves.append(Move((r, c), (r + moveAmount, c + 1), self.board, pawnPromotion = pawnPromotion))
                if (r + moveAmount, c + 1) == self.enPassantPossible:
                    attackingPiece = blockingPiece = False
                    if kingRow == r:
                         if kingCol < c: #king is the left of the pawn
                             #inside between king and pawn; outside range between pawn border
                             insideRange = range(kingCol + 1, c)
                             outsideRange = range(c + 2, 8)
                         else: #king is the right of the pawn
                             insideRange = range(kingCol - 1, c + 1, - 1)
                             outsideRange = range(c - 1, -1, -1)
                             for i in insideRange:
                                 if self.board[r][i] != "--": #some other piece beside en-passant pawn blocks
                                    blockingPiece = True
                             for i in outsideRange:
                                 square = self.board[r][i]
                                 if square[0] == enemyColor and (square[1] == "R" or square[1] == "Q"): #attacking
                                    attackingPiece = True
                                 elif square!= "--":
                                    blockingPiece = True
                    if not attackingPiece or blockingPiece:
                        moves.append(Move((r, c), (r + moveAmount, c + 1), self.board, enPassant = True))
                
        else: #black pawn moves 
             if self.board[r + 1][c] == "--": #1 square move
                if not piecePinned or pinDirection == (1, 0):
                    moves.append(Move((r, c), (r + 1, c), self.board))
                    if r == 1 and self.board[r + 2][c] == "--": #2 square moves
                        moves.append(Move((r, c), (r + 2, c), self.board))

             # captures   
             if c - 1 >= 0: #captures to the left
                if self.board[r + 1][c + 1][0] == 'w' : 
                    if not piecePinned or pinDirection == (1, -1):
                        moves.append(Move((r, c), (r + 1, c - 1), self.board))
                elif (r + 1, c - 1) == self.enPassantPossible:
                        moves.append(Move((r, c), (r + 1, c - 1), self.board, enPassantPossible = True))
             if c + 1 <= 7: #captures to the right
                if self.board[r + 1][c + 1][0] == 'w' : 
                    if not piecePinned or pinDirection == (1, 1):
                        moves.append(Move((r, c), (r + 1, c + 1), self.board))
                elif (r + 1, c + 1) == self.enPassantPossible:
                        moves.append(Move((r, c), (r + 1, c + 1), self.board, enPassantPossible = True))

    """
    Get rook moves moves given starting row and column, append the new moves to the list 'moves'
    """
    def getRookMoves(self, r, c, moves):
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                if self.board[r][c][1] != 'Q': #can't remove queen from pin on rook moves, only remove it on bishop moves
                    self.pins.remove(self.pins[i])
                break
        directions = ((-1, 0), (0, -1), (1, 0), (0, 1)) #up, lef, down, right
        enemyColor = "b" if self.whiteToMove else "w"
        for d in directions:
            for i in range(1, 8):
                endRow = r + d[0] * i
                endCol = c + d[1] * i
                if 0 <= endRow < 8 and 0 <= endCol < 8: #on board
                    if not piecePinned or pinDirection == d or pinDirection == (-d[0], -d[1]):
                        endPiece = self.board[endRow][endCol]
                        if endPiece == "--": #empty space valid
                            moves.append(Move((r, c), (endRow, endCol), self.board))
                        elif endPiece[0] == enemyColor: #enemy piece valid
                            moves.append(Move((r, c), (endRow, endCol), self.board))
                            break
                        else: #friendly piece invalid
                            break
                    else: #off board
                        break

    """
    Get knight moves given starting row and column, append the new moves to the list 'moves'
    """
    def getKnightMoves(self, r, c, moves):
        piecePinned = False
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                self.pins.remove(self.pins[i])
                break
        knightMoves = ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), ( 1, 2), (2, -1), (2, 1))
        allyColor = "w" if self.whiteToMove else "b"
        for m in knightMoves:
            endRow = r + m[0]
            endCol = c + m[1]
            if 0 <= endRow <8 and 0 <= endCol < 8:
                if not piecePinned:
                    endPiece = self.board[endRow][endCol]
                    if endPiece[0] != allyColor: #not an ally piece (empty or enmy piece)
                        moves.append(Move((r, c), (endRow, endCol), self.board))

    """
    Get bishop moves given starting row and column, append the new moves to the list 'moves'
    """
    def getBishopMoves(self, r, c, moves):
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                self.pins.removed(self.pins[i])
                break
        directions = ((-1, -1), (-1, 1), (1, -1), (1, 1)) #4 diaganols
        enemyColor  = "b" if self.whiteToMove else "w"
        for d in directions: 
            for i in range(1, 8): #bishop can move max of 7 squares
                endRow = r + d[0] * i
                endCol = c + d[1] * i
                if 0 <= endRow < 8 and 0 <= endCol < 8: #on board
                    if not piecePinned or pinDirection == d or pinDirection == (-d[0], -d[1]):
                        endPiece = self.board[endRow][endCol]
                        if endPiece == "--": #empty space valid
                            moves.append(Move((r, c), (endRow, endCol), self.board))
                        elif endPiece[0] == enemyColor: #enemy piece valid
                            moves.append(Move((r, c), (endRow, endCol), self.board))
                            break
                        else: #friendly piece invalid
                            break
                    else: #off board
                        break 

    """
    Get queen moves given starting row and column, append the new moves to the list 'moves'
    """
    def getQueenMoves(self, r, c, moves):
        self.getRookMoves(r, c, moves)
        self.getBishopMoves(r, c, moves)
        
    """
    Get king moves given starting row and column, append the new moves to the list 'moves'
    """
    def getKingMoves(self, r, c, moves):
        rowMoves = (-1, -1, -1, 0, 0, 1, 1, 1)
        colMoves = (-1, 0, 1, -1, 1, -1, 0, 1)
        allyColor = "w" if self.whiteToMove else "b"
        for i in range(8):
            endRow = r + rowMoves[i]
            endCol = c + colMoves[i]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                endPiece = self.board[endRow][endCol]
                if endPiece[0] != allyColor: #not an ally piece (empty or enemy piece)
                    #place king on end square and check for checks
                    if allyColor == 'w':
                        self.whiteKingLocation = (endRow, endCol)
                    else:
                        self.blackKingLocation = (endRow, endCol)
                    inCheck, pins, checks = self.checkForPinsAndChecks()
                    if not inCheck:
                        moves.append(Move((r, c), (endRow, endCol), self.board))
                    #place king back on original location
                    if allyColor == 'w':
                        self.whiteKingLocation = (r, c)
                    else:
                        self.blackKingLocation = (r, c) 
        self.getCastleMoves(r, c, moves, allyColor)

    """
    Generate castle moves for the king at (r,c) and add them to the list of moves
    """
    def getCastleMoves(self, r, c, moves, allyColor):
        inCheck = self.squareUnderAttack(r, c, allyColor)
        if inCheck:
            return #can't castle in check
        if (self.whiteToMove and self.currentCastlingRight.wks) or (not self.whiteToMove and self.currentCastlingRight.bks): #can't castle if given up rights
            self.getKingsideCastleMoves(r, c, moves, allyColor)
        if (self.whiteToMove and self.currentCastlingRight.wqs) or (not self.whiteToMove and self.currentCastlingRight.bqs):
            self.getQueensideCaslteMoves(r, c, moves, allyColor)
    

    """
    Generate kingside castle moves for the king at (r, c). This method will only be called if player still has castle rights kingside.
    """
    def getKingsideCaslteMoves(self, r, c, moves, allyColor):
        #check if two square between king and rook are clear and not under attack
        if self.board[r][c + 1] == '--' and self.board[r][c + 2] == '--' and \
            not self.squareUnderAttack(r, c + 1, allyColor) and not self.squareUnderAttack (r, c + 2, allyColor):
            moves.append(Move((r, c), (r, c + 2), self.board, castle = True))

    """
    Generate queenside castle moves for the king at (r, c). This method will only be called if player still has castle rights queenside
    """
    def getQueensideCastleMoves(self, r, c, moves, allyColor):
        #check if three square between king and rook are clear and two squares left of king are not under attack
        if self.board[r][c - 1] == '--' and self.board[r][c - 2] == '--' and self.board[r][c - 3] == '--' and \
            not self.squareUnderAttack(r, c - 1, allyColor) and not self.squareUnderAttack (r, c - 2, allyColor):
            moves.append(Move((r, c), (r, c - 2), self.board, castle = True))

    """
    Returns if the square is under attack
    """
    def squareUnderAttack(self, r, c, allyColor):
        #check outward from square
        enemyColor = 'w' if allyColor == 'b' else 'b'
        directions = ((-1, 0), (0, -1), (1, 0), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1))
        for j in range(len(directions)):
            d = directions[j]
            for i in range(1, 8):
                endRow = r + d[0] * i
                endCol = c + d[1] * i
                if 0 <= endRow < 8 and 0 <= endCol < 8:
                    endPiece = self.board[endRow][endCol]
                    if endPiece[0] == allyColor: #no attack from that direction
                        break
                    elif endPiece[0] == enemyColor:
                        type == endPiece[1]
                        #5 possibilities here in this complex conditional
                        #1.) orthogonally away from king and piece is a rook
                        #2.) diagonally away from king and peice is a bishop
                        #3.) 1 square away diagonally from king and piece is a pawn
                        #4.) any direction and piece is a queen
                        #5.) any direction 1 square away and piece is king (this is necessary to prevent a king to move a square controlled by another king)
                        if (0 <= j <= 3 and type == 'R') or \
                           (4 <= j <= 7 and type == 'B') or \
                           (i == 1 and type == 'p' and ((enemyColor == 'w' and 6 <= j <= 7) or (enemyColor == 'b' and 4 <= j <= 5))) or \
                           (type == 'Q') or (i == 1 and type == 'K'):
                           return True
                        else: #enemy piece not applying check:
                           break
                else: 
                        break #off board   
        #check for knight checks
        knightMoves = ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1))
        for m in knightMoves:
            endRow = r + m[0]
            endCol = c + m[1]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                 endPiece = self.board[endRow][endCol]
                 if endPiece[0] == enemyColor and endPiece[1] == 'N': #enemy knight attack king
                     return True
            return False  
    
    """
    Returns if the player is in check, a list of pins, and a list of checks
    """
    def checkForPinsAndChecks(self):
        pins = [] #squares where the allied pinned piece is and the direction pinned from
        checks = [] #squares where enemy is applying a check
        inCheck = False
        if self.whiteToMove:
            enemyColor = "b"
            allyColor = "w"
            startRow = self.whiteKingLocation[0]
            startCol = self.whiteKingLocation[1]
        else:
            enemyColor = "w"
            allyColor = "b"
            startRow = self.blackKingLocation[0]
            startCol = self.blackKingLocation[1]
        #check outward from king for pins and checks, keep track of pins
        directions = ((-1, 0), (0, -1), (1, 0), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1))
        for j in range(len(directions)):
            d = directions[j]
            possiblePin = () #reset possible pins
            for i in range(1, 8):
                endRow = startRow + d[0] * i
                endCol = startCol + d[1] * i
                if 0 <= endRow < 8 and 0 <= endCol < 8:
                    endPiece = self.board[endRow][endCol]
                    if endPiece[0] == allyColor and endPiece[1] != 'K':
                        if possiblePin == (): #1st allied piece could be pinned
                           possiblePin = (endRow, endCol, d[0], d[1])
                        else: #2nd allied piece, so no pin or check possible in this direction
                            break
                    elif endPiece[0] == enemyColor:
                        type == endPiece[1]
                        #5 possibilities here in this complex conditional
                        #1.) orthogonally away from king and piece is a rook
                        #2.) diagonally away from king and peice is a bishop
                        #3.) 1 square away diagonally from king and piece is a pawn
                        #4.) any direction and piece is a queen
                        #5.) any direction 1 square away and piece is king (this is necessary to prevent a king to move a square controlled by another king)
                        if (0 <= j <= 3 and type == 'R') or \
                           (4 <= j <= 7 and type == 'B') or \
                           (i == 1 and type == 'p' and ((enemyColor == 'w' and 6 <= j <= 7) or (enemyColor == 'b' and 4 <= j <= 5))) or \
                           (type == 'Q') or (i == 1 and type == 'K'):
                           if possiblePin == (): #no piece blocking, so check
                               inCheck = True
                               checks.append((endRow, endCol, d[0], d[1]))
                               break
                           else: #piece blocking so pin
                               pins.append(possiblePin)
                               break
                        else: #enemy piece not applying check
                            break
                    else: 
                        break #off board   
        #check for knight checks
        knightMoves = ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1))
        for m in knightMoves:
            endRow = startRow + m[0]
            endCol = startCol + m[1]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                endPiece = self.board[endRow][endCol]
                if endPiece[0] == enemyColor and endPiece[1] == 'N': #enemy knight attack king
                    inCheck = True
                    checks.append((endRow, endCol, m[0], m[1]))
        return inCheck, pins, checks

    """
    Update the castle rights given the move
    """
    def updateCastleRights(self, move):
        if move.pieceMoved == 'wk':
            self.currentCastlingRight.wks = False
            self.currentCastlingRight.wqs = False
        elif move.pieceMoved == 'bk':
            self.currentCastlingRight.bks = False
            self.currentCastlingRight.bqs = False
        elif move.pieceMoved == 'wR':
            if move.startRow == 7:
                if move.startCol == 0: #left rook
                    self.currentCastlingRight.wqs = False
                elif move.startCol == 7: #right rook
                    self.currentCastlingRight.wks = False
        elif move.pieceMoved == 'bR':
            if move.startRow == 0:
                if move.startCol == 0: #left rook
                    self.currentCastlingRight.bqs = False
                elif move.startCol == 7: #right rook
                    self.currentCastlingRight.bks = False
        
        #if a rook is captured
        if move.pieceCaptured == 'wR':
            if move.endRow == 7:
                if move.endCol == 0:
                    self.currentCastlingRight.wqs = False
                elif move.endCol == 7:
                    self.currentCastlingRight.wks = False
        elif move.pieceCaptured == 'bR':
            if move.endRow == 0:
                if move.endCol == 0:
                    self.currentCastlingRight.bqs = False
                elif move.endCol == 7:
                    self.currentCastlingRight.bks = False

class CastleRights():
    def __int__(self, wks, bks, wqs, bqs):
        self.wks = wks
        self.bks = bks
        self.wqs = wqs
        self.bqs = bqs

class Move():
    # maps keys to values
    # key : value
    ranksToRows = {"1": 7, "2" : 6, "3": 5, "4": 4,
                   "5": 3, "6" : 2, "7": 1, "8": 0}
    rowsToRanks = {v: k for k, v in ranksToRows.items()}
    filesToCols = {"a": 0, "b": 1, "c": 2, "d": 3,
                   "e": 4, "f": 5, "g": 6, "h": 7}
    colsToFiles = {v: k for k, v in filesToCols.items()}

    def __int__(self, startSq, endSq, board, enPassant = False, pawnPromotion = False, castle = False):
        self.startRow = startSq[0]
        self.startCol = startSq[1]
        self.endRow = endSq[0]
        self.endCol = endSq[1]
        self.pieceMoved = board[self.startRow][self.startCol]
        self.pieceCaptured = board[self.endRow][self.endCol]
        self.enPassant = enPassant
        self.PawnPromotion = pawnPromotion     
        #castle move
        self.castle = castle
        if enPassant:
            self.pieceCaptured = 'bp' if self.pieceMoved == 'wp' else 'wp' #enpassant captures opposite colored pawn
        self.isCapture = self.pieceCaptured != '--' 
        self.moveID = self.startRow * 1000 + self.startCol * 100 + self.endRow *10 + self.endCol
        

    """
    Overriding the equals method
    """
    def __eq__(self, other):
        if isinstance(other, Move):
            return self.moveID == other.moveID
        return False

    def getChessNotation(self):
        #you can add to make this like real chess notation
        return self.getRankFile(self.startRow, self.startCol) + self.getRankFile(self.endRow, self.endCol)

    def getRankFile(self, r, c):
        return self.colsToFiles[c] + self.rowsToRanks[r]
    
    #overriding the str() funtion
    def __str__(self):
        #castle move
        if self.castle:
            return "O-O" if self.endcol == 6 else "O-O-O" 
        
        endSquare = self.getRankFile(self.endRow, self.endCol)
        #pawn moves
        if self.pieceMoved[1] == 'p':
            if self.isCapture:
                return self.colsToFiles[self.startCol] + 'x' + endSquare
            else:
                return endSquare

            #pawn promotions


        #two of the same type of piece moving to a square, Nbd2 if both knights can move to d2

        #also adding + for check move, and # for checkmate move

        #piece moves
        moveString = self.pieceMoved[1]
        if self.isCapture:
            moveString += 'x'
        return moveString + endSquare
        
