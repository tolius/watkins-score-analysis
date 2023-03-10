import requests
import json
import subprocess
from chess.variant import AntichessBoard


class Score:
    def __init__(self, score=0, game_id=""):
        self.score = score
        self.game_id = game_id

    def __repr__(self):
        return f"{self.score} /{self.game_id}/"


def get_uci_moves(san_moves):
    moves = []
    board = AntichessBoard()
    for san in san_moves:
        move = board.parse_san(san)
        moves.append(board.uci(move))
        board.push(move)
    return moves


def main():
    url = "https://lichess.org/api/tournament/dPFhERel/games"
    watkins_path = "C:\\path\\to\\Watkins-reader.exe"
    solution_path = "C:\\path\\to\\the\\solution\\file\\e3wins.rev4"
    # Input: 'e2e3 g7g5 f1a6\n' Output: 'b7a6\n' if it's the solution else 'null\n'
    # Info: https://magma.maths.usyd.edu.au/~watkins/LOSING_CHESS/CombinedJan05.tar
    watkins_engine = subprocess.Popen([watkins_path, solution_path], bufsize=1, stdout=subprocess.PIPE,
                                      stdin=subprocess.PIPE, universal_newlines=True)
    headers = {'Accept': "application/x-ndjson"}
    r = requests.get(url, headers=headers, allow_redirects=True)
    if r.status_code != 200:
        raise Exception(f"ERROR /api/tournament/: Status Code {r.status_code}")
    content = r.content.decode("utf-8")
    lines = content.split("\n")[:-1]
    data = [json.loads(line) for line in lines]
    player_scores = {}
    print("Processing games", end="")
    n = 0
    for game in data:
        game_id = game['id']
        player_white = game['players']['white']['user']['name']
        player_black = game['players']['black']['user']['name']
        winner = game.get('winner', "draw")
        san_moves = game['moves'].split()
        moves = [] if (not san_moves) or (san_moves[0] != "e3") else get_uci_moves(san_moves)
        i = 0
        for i in range(len(moves)):
            if i % 2 == 1:
                continue
            moves_i = f"{' '.join(moves[:i + 1])}\n"
            watkins_engine.stdin.write(moves_i)
            str_move = watkins_engine.stdout.readline()
            assert len(str_move) >= 5 and str_move[-1] == '\n'
            str_move = str_move[:-1]
            if len(str_move) < 4 or len(str_move) > 5 or str_move.lower() == "null":
                break
        win_player = player_white if winner == "white" \
            else player_black if winner == "black" \
            else f"{player_white} = {player_black}"
        new_score = Score(min(i, max(0, len(moves) - 1)) // 2, game_id)
        old_score = player_scores.get(win_player)
        if (old_score is None) or (new_score.score > old_score.score):
            player_scores[win_player] = new_score
        n += 1
        if n % 10 == 0:
            print(".", end="")
    items = sorted(player_scores.items(), key=lambda it: it[1].score, reverse=True)
    print(f"\nTournament info: {len(player_scores)} players, {len(data)} games")
    print("Top 10 Watkins scores:")
    i = 1
    for item in items:
        print(f"{i:2}. #{item[1].score:02} - https://lichess.org/{item[1].game_id} - {item[0]}")
        if i >= 10:
            break
        i += 1

    # Output:
    # Tournament info: 68 players, 218 games
    # Top 10 Watkins scores:
    #  1. #13 - https://lichess.org/w8KyGNVN - Gary_JBS
    #  2. #11 - https://lichess.org/moKQV4Is - randimatrix
    #  3. #09 - https://lichess.org/GTDQG8lQ - wayne_bruce
    #  4. #09 - https://lichess.org/vXv9ZjDV - MiladLouak0
    #  5. #09 - https://lichess.org/NoJjtrlY - SuperSrbinRS
    #  6. #09 - https://lichess.org/QvvWoOUu - Afiq2017
    #  7. #08 - https://lichess.org/HDinpqW4 - dSinner
    #  8. #06 - https://lichess.org/ixcgC7q9 - mental_suicide
    #  9. #06 - https://lichess.org/8ylICEio - Serge007
    # 10. #05 - https://lichess.org/mel1LshW - L0g1cal-N0de


if __name__ == "__main__":
    main()
