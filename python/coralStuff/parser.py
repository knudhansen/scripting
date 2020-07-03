import argparse
import sys

# The scripts relies on:
# - the first line of the table containing the dates of the observations.
# - the only acceptable text in the first column passed the 2 first line is 'Platine', which is ignored, or a platine name.
# - empty dates should have less than 7 columns. Those are totally ignored.
# - every data on a 'platine' to have a platine name in the first row of the first line of the observation.
# - the data tables do start on a fix column relative to the observation dates in first row (observation data column + 2).
# - the data tables always having the 'dessus', 'bords', 'dessous', 'Total' in that order.
# - the data tables have a Total line after the family lines.
# - the data tables (with the different families and the different positions) does not have empty lines.
#   An empty line is considered as the end of the data. Further data will be ignored until a new platine is detected in first column.
# - there is an empty line under the data before other tables are added. The tables below the data are ignored.
# - all data for a given 
parser = argparse.ArgumentParser(prog='PROG')
parser.add_argument('-i', '--input', required=True, help='input file')
parser.add_argument('-l', '--location', help='location from where the samples where collected', default='')
parser.add_argument('-d', '--depth', help='depth at which the samples where collected', default='')
args = parser.parse_args()

input = open(args.input)

dataSeries = None

for row in input.readlines():
    
    columns = row[:-1].split(',')

    ## getting the dates form the first line
    if not dataSeries:
        dataSeries = {}
        dataSeries['title'] = columns[0]
        dataSeries['observations'] = []
        for columnIndex in range (1,len(columns)-1):
            if columns[columnIndex] != '':
                dataSeries['observations'].append({})
                dataSeries['observations'][-1]['date'] = columns[columnIndex]
                dataSeries['observations'][-1]['scol'] = columnIndex
                if len(dataSeries['observations']) > 1:
                    dataSeries['observations'][-2]['ecol'] = columnIndex - 1
                dataSeries['observations'][-1]['details'] = None
                dataSeries['observations'][-1]['data'] = []
        dataSeries['observations'][-1]['ecol'] = len(columns) - 1

    else:
        for observation in dataSeries['observations']:

            if observation['details'] == None:
                ## getting details from the second line
                observation['details'] = columns[observation['scol']]
            elif columns[0] and columns[0] != 'Platine':
                observation['data'].append({})
                observation['data'][-1]['platine'] = columns[0]
                observation['data'][-1]['plaque'] = columns[observation['scol']]
                observation['data'][-1]['familles'] = []
                observation['data'][-1]['done'] = False
            elif len(observation['data']) > 0 and (observation['ecol'] - observation['scol'] >= 7) and columns[observation['scol']+2] and not observation['data'][-1]['done']:
                observation['data'][-1]['familles'].append({})
                famille = observation['data'][-1]['familles'][-1]
                famille['name'] = columns[observation['scol']+2]
                famille['positions'] = {}
                famille['positions']['dessus'] = 0
                famille['positions']['bord'] = 0
                famille['positions']['dessous'] = 0
                famille['total'] = 0
                if columns[observation['scol']+3]:
                    famille['positions']['dessus'] = int(columns[observation['scol']+3])
                if columns[observation['scol']+4]:
                    famille['positions']['bord'] = int(columns[observation['scol']+4])
                if columns[observation['scol']+5]:
                    famille['positions']['dessous'] = int(columns[observation['scol']+5])
                if columns[observation['scol']+6]:
                    famille['total'] = int(columns[observation['scol']+6])
            elif len(observation['data']) > 0 and not columns[observation['scol']+2]:
                ## finish capturing on empty 
                observation['data'][-1]['done'] = True

for observation in dataSeries['observations']:
    for data in observation['data']:
        positionTotalsCalc = {'dessus': 0, 'bord': 0, 'dessous': 0}
        positionTotalsRead = {'dessus': 0, 'bord': 0, 'dessous': 0}
        for famille in data['familles']:
            if famille['total']!=famille['positions']['dessus']+famille['positions']['bord']+famille['positions']['dessous']:
                sys.stderr.write("WARNING: family total error in file %s for (%s: %s: %s: %s) -- read %d, expected %d\n" % (args.input, observation['date'], data['platine'], data['plaque'], famille['name'], famille['total'], famille['positions']['dessus']+famille['positions']['bord']+famille['positions']['dessous']))
            if famille['name'] != 'Total':
                positionTotalsCalc['dessus']  = positionTotalsCalc['dessus']  + famille['positions']['dessus']
                positionTotalsCalc['bord']    = positionTotalsCalc['bord']    + famille['positions']['bord']
                positionTotalsCalc['dessous'] = positionTotalsCalc['dessous'] + famille['positions']['dessous']
            else:
                positionTotalsRead['dessus']  = famille['positions']['dessus']
                positionTotalsRead['bord']    = famille['positions']['bord']
                positionTotalsRead['dessous'] = famille['positions']['dessous']
        for position in ['dessus', 'bord', 'dessous']:
            if positionTotalsCalc[position] != positionTotalsRead[position]:
                sys.stderr.write("WARNING: position total error in file %s for (%s: %s: %s: %s:%s) -- read %d, expected %d\n" % (args.input, observation['date'], data['platine'], data['plaque'], famille['name'], position, positionTotalsRead[position], positionTotalsCalc[position]))

print "%s, %s, %s, %s, %s, %s, %s" % ('date', 'location', 'depth', 'platine', 'plaque', 'famille', 'nombre')
for observation in dataSeries['observations']:
    for data in observation['data']:
        for famille in data['familles']:
            if famille['name'] != 'Total':
                print "%s, %s, %s, %s, %s, %s, %d" % (observation['date'], args.location, args.depth, data['platine'], data['plaque'], famille['name'],famille['total'])
