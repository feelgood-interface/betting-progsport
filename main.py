import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
from functools import cmp_to_key
from prettytable import PrettyTable


@dataclass
class Fixture:
    league: str
    team_a: str
    team_b: str
    predict_win_a: float
    predict_win_b: float
    odds_win_a: float
    odds_win_b: float
    spread: float
    predict_spread_a: float
    predict_spread_b: float
    total: float
    predict_total_under: float
    predict_total_over: float
    predict_total: float
    result_a: str
    result_b: str


def is_float(string):
    try:
        float(string)
        return True
    except ValueError:
        return False


def scrape_fixtures():
    # url = 'http://www.progsport.com/basketball/bsk-predictions-210129.html'
    url = 'http://www.progsport.com/'
    request = requests.get(url)
    request.raise_for_status()

    soup = BeautifulSoup(request.content, 'lxml')

    # fixture_table = soup.findAll('table', {'id': 'anyid'})

    fixture_elements = soup.findAll('tr', {'class': ['F1', 'F2']})

    fixtures = []
    for fixture_element in fixture_elements:
        children = fixture_element.findChildren('td', recursive=False)
        if len(children) != 15:
            continue
        league = children[1].text
        team = children[2].text.split('-')
        team_a = team[0].strip()
        team_b = team[1].strip()
        predict_win_a = float(children[3].text) if is_float(children[3].text) else None
        predict_win_b = float(children[4].text) if is_float(children[4].text) else None
        odds_win_a = float(children[5].text) if is_float(children[5].text) else None
        odds_win_b = float(children[6].text) if is_float(children[6].text) else None
        spread = float(children[7].text) if is_float(children[7].text) else None
        predict_spread_a = float(children[8].text) if is_float(children[8].text) else None
        predict_spread_b = float(children[9].text) if is_float(children[9].text) else None
        total = float(children[10].text) if is_float(children[10].text) else None
        predict_total_under = float(children[11].text) if is_float(children[11].text) else None
        predict_total_over = float(children[12].text) if is_float(children[12].text) else None
        predict_total = float(children[13].text) if is_float(children[13].text) else None
        result = children[14].text
        if len(result) > 0:
            result = result.split('-')
            result_a = result[0]
            result_b = result[1]
        else:
            result_a = ''
            result_b = ''

        fixture = Fixture(
            league,
            team_a,
            team_b,
            predict_win_a,
            predict_win_b,
            odds_win_a,
            odds_win_b,
            spread,
            predict_spread_a,
            predict_spread_b,
            total,
            predict_total_under,
            predict_total_over,
            predict_total,
            result_a,
            result_b
        )

        fixtures.append(fixture)

    return fixtures


def compare_spread(fixture1, fixture2):
    fixture1_has_value = fixture1.predict_spread_a is not None and fixture1.predict_spread_b is not None
    fixture2_has_value = fixture2.predict_spread_a is not None and fixture2.predict_spread_b is not None
    if fixture1_has_value and fixture2_has_value:
        fixture1_max_spread = max(fixture1.predict_spread_a, fixture1.predict_spread_b)
        fixture2_max_spread = max(fixture2.predict_spread_a, fixture2.predict_spread_b)
        if fixture1_max_spread > fixture2_max_spread:
            return -1
        else:
            return 1
    elif fixture1_has_value and not fixture2_has_value:
        return -1
    else:
        return 1


def compare_total(fixture1, fixture2):
    fixture1_has_value = fixture1.predict_total_under is not None and fixture1.predict_total_over is not None
    fixture2_has_value = fixture2.predict_total_under is not None and fixture2.predict_total_over is not None
    if fixture1_has_value and fixture2_has_value:
        fixture1_max_total = max(fixture1.predict_total_under, fixture1.predict_total_over)
        fixture2_max_total = max(fixture2.predict_total_under, fixture2.predict_total_over)
        if fixture1_max_total > fixture2_max_total:
            return -1
        else:
            return 1
    elif fixture1_has_value and not fixture2_has_value:
        return -1
    else:
        return 1


def compare_win(fixture1, fixture2):
    fixture1_has_value = fixture1.predict_win_a is not None and fixture1.odds_win_a is not None
    fixture2_has_value = fixture2.predict_win_a is not None and fixture2.odds_win_a is not None
    if fixture1_has_value and fixture2_has_value:
        fixture1_max_value = max(calculate_value(fixture1.odds_win_a, fixture1.predict_win_a),
                                 calculate_value(fixture1.odds_win_b, fixture1.predict_win_b))
        fixture2_max_value = max(calculate_value(fixture2.odds_win_a, fixture2.predict_win_a),
                                 calculate_value(fixture2.odds_win_b, fixture2.predict_win_b))
        if fixture1_max_value > fixture2_max_value:
            return -1
        else:
            return 1
    elif fixture1_has_value and not fixture2_has_value:
        return -1
    else:
        return 1


def calculate_value(odds, predict_win):
    if odds is None or predict_win is None:
        return None
    # Value = (Probability * Decimal Odds) – 1
    value = (predict_win / 100 * odds) - 1
    return value


def print_best_predict(fixtures, top_n=5):
    fixtures_sorted_win = sorted(fixtures, key=cmp_to_key(compare_win))
    # print([calculate_value(x.odds_win_a, x.predict_win_a) for x in fixtures_sorted_win])
    # print([calculate_value(x.odds_win_b, x.predict_win_b) for x in fixtures_sorted_win])
    table = PrettyTable(['Fixture', 'Predict A', 'Predict B', 'Odds A', 'Odds B', 'Value'])
    table.align['Fixture'] = 'l'
    for i in range(top_n):
        fixture = fixtures_sorted_win[i]
        value = max(calculate_value(fixture.odds_win_a, fixture.predict_win_a),
                    calculate_value(fixture.odds_win_b, fixture.predict_win_b))
        table.add_row([f'{fixture.team_a} vs {fixture.team_b}', fixture.predict_win_a, fixture.predict_win_b,
                       fixture.odds_win_a, fixture.odds_win_b, round(value, 3)])
    print(table)

    fixtures_sorted_spread = sorted(fixtures, key=cmp_to_key(compare_spread))
    # print([x.predict_spread_a for x in fixtures_sorted_spread])
    # print([x.predict_spread_b for x in fixtures_sorted_spread])
    table = PrettyTable(['Fixture', 'Spread', 'Team A', 'Team B'])
    table.align['Fixture'] = 'l'
    for i in range(top_n):
        fixture = fixtures_sorted_spread[i]
        if fixture.spread is not None:
            table.add_row([f'{fixture.team_a} vs {fixture.team_b}', fixture.spread, fixture.predict_spread_a,
                           fixture.predict_spread_b])
    print(table)

    fixtures_sorted_total = sorted(fixtures, key=cmp_to_key(compare_total))
    # print([x.predict_total_under for x in fixtures_sorted_total])
    # print([x.predict_total_over for x in fixtures_sorted_total])
    table = PrettyTable(['Fixture', 'Total', 'Under', 'Over', 'Predicted Total'])
    table.align['Fixture'] = 'l'
    for i in range(top_n):
        fixture = fixtures_sorted_total[i]
        if fixture.total is not None:
            table.add_row([f'{fixture.team_a} vs {fixture.team_b}', fixture.total, fixture.predict_total_under,
                           fixture.predict_total_over, fixture.predict_total])
    print(table)


def main():
    fixtures = scrape_fixtures()
    print_best_predict(fixtures)


if __name__ == '__main__':
    main()
