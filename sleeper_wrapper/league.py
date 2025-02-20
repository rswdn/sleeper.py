from audioop import tostereo
from urllib.parse import non_hierarchical
from .base_api import BaseApi
from .stats import Stats

class League(BaseApi):

        def __init__(self, league_id):
                self.league_id = league_id
                self._base_url = "https://api.sleeper.app/v1/league/{}".format(self.league_id)
                self._league = self._call(self._base_url)

        def get_league(self):
                return self._league

        def get_rosters(self):
                return self._call("{}/{}".format(self._base_url,"rosters"))

        def get_users(self):
                return self._call("{}/{}".format(self._base_url,"users"))

        def get_matchups(self, week):
                return self._call("{}/{}/{}".format(self._base_url,"matchups", week))

        def get_playoff_winners_bracket(self):
                return self._call("{}/{}".format(self._base_url,"winners_bracket"))

        def get_playoff_losers_bracket(self):
                return self._call("{}/{}".format(self._base_url,"losers_bracket"))

        def get_transactions(self, week):
                return self._call("{}/{}/{}".format(self._base_url,"transactions", week))

        def get_traded_picks(self):
                return self._call("{}/{}".format(self._base_url,"traded_picks"))

        def get_all_drafts(self):
                return self._call("{}/{}".format(self._base_url, "drafts"))

        def map_users_to_team_name(self, users):
                """ returns dict {user_id:team_name}"""
                users_dict = {}

                #Maps the user_id to team name for easy lookup
                for user in users:
                        try:
                                users_dict[user["user_id"]] = user["username"]
                        except:
                                users_dict[user["user_id"]] = user["display_name"]
                return users_dict

        def get_standings(self, rosters, users):
                users_dict = self.map_users_to_team_name(users)

                roster_standings_list = []
                for roster in rosters:
                        wins = roster["settings"]["wins"]
                        points = roster["settings"]["fpts"]
                        points_decimal = roster["settings"]["fpts_decimal"]
                        points_total = str(points) + '.' + str(points_decimal)
                        fpts_against = roster["settings"]["fpts_against"]
                        fpts_decimal = roster["settings"]["fpts_against_decimal"]
                        fpts_against_total = str(fpts_against) + '.' + str(fpts_decimal)
                        name = roster["owner_id"]
                        losses = roster["settings"]["losses"]
                        if name is not None:
                                roster_tuple = (wins, losses, points_total, fpts_against_total, users_dict[name])
                        else:
                                roster_tuple = (wins, losses, points_total, fpts_against_total, None)
                        roster_standings_list.append(roster_tuple)

                roster_standings_list.sort(reverse = 1)

                clean_standings_list = []
                for item in roster_standings_list:
                        clean_standings_list.append((item[4], str(item[0]), str(item[1]), str(item[2]),str(item[3])))
                
                return clean_standings_list

        def map_rosterid_to_ownerid(self, rosters ):
                """returns: dict {roster_id:[owner_id,pts]} """
                result_dict = {}
                for roster in rosters:
                        roster_id = roster["roster_id"]
                        owner_id = roster["owner_id"]
                        result_dict[roster_id] = owner_id

                return result_dict

        
        def get_scoreboards(self, rosters, matchups, users, week):
                """ returns dict {matchup_id:[(team_name,score), (team_name, score)]}"""
                roster_id_dict = self.map_rosterid_to_ownerid(rosters)


                if len(matchups) == 0:
                        return None

                #Get the users to team name stats
                users_dict = self.map_users_to_team_name(users)


                #map roster_id to points
                scoreboards_dict = {}

                for team in matchups:
                        matchup_id = team["matchup_id"]
                        current_roster_id = team["roster_id"]
                        owner_id = roster_id_dict[current_roster_id]
                        if owner_id is not None:
                                team_name = users_dict[owner_id]
                        else:
                                team_name = "Team name not available"

                        team_score = team['points']
                        if team_score is None:
                                team_score = 0

                        team_score_tuple = (team_name, team_score)
                        if matchup_id not in scoreboards_dict:
                                scoreboards_dict[matchup_id] = [team_score_tuple]
                        else:
                                scoreboards_dict[matchup_id].append(team_score_tuple)
                return scoreboards_dict

                    
        def get_lineups(self,rosters,matchups,users,week):
                """ returns dict {matchup_id:[(team_name,score), (team_name, score)]}"""
                roster_id_dict = self.map_rosterid_to_ownerid(rosters)

                if len(matchups) == 0:
                        return None

                #Get the users to team name stats
                users_dict = self.map_users_to_team_name(users)


                #map roster_id to startes
                lineups = []
                names = []
                for team in matchups:
                        matchup_id = team["matchup_id"]
                        current_roster_id = team["roster_id"]
                        owner_id = roster_id_dict[current_roster_id]

                        if owner_id is not None:
                                team_name = users_dict[owner_id]
                        else:
                                team_name = "Team name not available"

                        starters = team['starters']
                        if starters is None:
                                starters = 0

                        lineups.append(starters)
                        names.append(team_name)

                return names,lineups

        def get_waivers(self,users,transactions):
                """ returns array [username,transaction type,status,adds,drops]"""
                users_dict = self.map_users_to_team_name(users)

                if len(transactions) == 0:
                        return None
                
                waiver_name = []
                waiver_type = []
                waiver_status = []
                waiver_add = []
                waiver_drops = []
                for i in transactions:
                        roster_id = i['creator']
                        trans_type = i['type']
                        trans_status = i['status']
                        trans_add = i['adds']
                        trans_drops = i['drops']

                        if roster_id is not None:
                                team_name = users_dict[roster_id]
                        else:
                                team_name = 'No team found'
                        waiver_name.append(team_name)
                        waiver_type.append(trans_type)
                        waiver_status.append(trans_status)
                        waiver_add.append(trans_add)
                        waiver_drops.append(trans_drops)
                return waiver_name,waiver_type,waiver_status,waiver_add,waiver_drops




        def get_close_games(self, scoreboards, close_num):
                """ -Notes: Need to find a better way to compare scores rather than abs value of the difference of floats. """
                close_games_dict = {}
                for key in scoreboards:
                        team_one_score = scoreboards[key][0][1]
                        team_two_score = scoreboards[key][1][1]

                        if abs(team_one_score-team_two_score) < close_num:
                                close_games_dict[key] = scoreboards[key]
                return close_games_dict

        def empty_roster_spots(self):
                pass

        def get_negative_scores(self, week):
                pass

        def get_rosters_players(self):
                pass
