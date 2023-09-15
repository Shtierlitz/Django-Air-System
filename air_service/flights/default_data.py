from datetime import datetime, timedelta
import random as rn
from django.apps import apps
from django.utils import timezone
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'air_service.settings')
django.setup()
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from flights.tasks import flight_expiration_task
from flights.models import *



time_list = [i for i in range(23)]

dep_list = [
    timezone.make_aware(
        datetime(2023, rn.randint(9, 12), rn.randint(1, 27), rn.randint(1, 23), rn.choice([0, 30]))) for
    i in range(100)]
flight_dict = {}
for i, j in enumerate(dep_list):
    flight_dict[i] = {'dep_time': j}
    n = j + timedelta(hours=rn.randint(1, 7)) + timedelta(minutes=rn.choice([0, 30]))
    naive_n = datetime(n.year, n.month, n.day, n.hour, n.minute, n.second, n.microsecond)
    flight_dict[i].update({'arr_time': timezone.make_aware(naive_n)})

airport_dict = {
    1: {'name': 'Hartsfield-Jackson Atlanta International Airport', 'code': 'ATL', 'city': 'Atlanta', 'country': 'US'},
    2: {'name': 'Los Angeles International Airport', 'code': 'LAX', 'city': 'Los Angeles', 'country': 'US'},
    3: {'name': "Chicago O'Hare International Airport", 'code': 'ORD', 'city': 'Chicago', 'country': 'US'},
    4: {'name': 'Dallas/Fort Worth International Airport', 'code': 'DFW', 'city': 'Dallas', 'country': 'US'},
    5: {'name': 'Denver International Airport', 'code': 'DEN', 'city': 'Denver', 'country': 'US'},
    6: {'name': 'John F. Kennedy International Airport', 'code': 'JFK', 'city': 'New York', 'country': 'US'},
    7: {'name': 'San Francisco International Airport', 'code': 'SFO', 'city': 'San Francisco', 'country': 'US'},
    8: {'name': 'Seattle-Tacoma International Airport', 'code': 'SEA', 'city': 'Seattle', 'country': 'US'},
    9: {'name': 'Miami International Airport', 'code': 'MIA', 'city': 'Miami', 'country': 'US'},
    10: {'name': 'Orlando International Airport', 'code': 'MCO', 'city': 'Orlando', 'country': 'US'},
    11: {'name': 'Newark Liberty International Airport', 'code': 'EWR', 'city': 'Newark', 'country': 'US'},
    12: {'name': 'Detroit Metropolitan Airport', 'code': 'DTW', 'city': 'Detroit', 'country': 'US'},
    13: {'name': 'Minneapolis-Saint Paul International Airport', 'code': 'MSP', 'city': 'Minneapolis', 'country': 'US'},
    14: {'name': 'George Bush Intercontinental Airport', 'code': 'IAH', 'city': 'Houston', 'country': 'US'},
    15: {'name': 'Phoenix Sky Harbor International Airport', 'code': 'PHX', 'city': 'Phoenix', 'country': 'US'},
    16: {'name': 'Philadelphia International Airport', 'code': 'PHL', 'city': 'Philadelphia', 'country': 'US'},
    17: {'name': 'LaGuardia Airport', 'code': 'LGA', 'city': 'New York', 'country': 'US'},
    18: {'name': 'Charlotte Douglas International Airport', 'code': 'CLT', 'city': 'Charlotte', 'country': 'US'},
    19: {'name': 'San Diego International Airport', 'code': 'SAN', 'city': 'San Diego', 'country': 'US'},
    20: {'name': 'Tampa International Airport', 'code': 'TPA', 'city': 'Tampa', 'country': 'US'},
    21: {'name': 'Portland International Airport', 'code': 'PDX', 'city': 'Portland', 'country': 'US'},
    22: {'name': 'Luis Muñoz Marín International Airport', 'code': 'SJU', 'city': 'San Juan', 'country': 'US'},
    23: {'name': 'Memphis International Airport', 'code': 'MEM', 'city': 'Memphis', 'country': 'US'},
    24: {'name': 'Oakland International Airport', 'code': 'OAK', 'city': 'Oakland', 'country': 'US'},
    25: {'name': 'Washington Dulles International Airport', 'code': 'IAD', 'city': 'Washington D.C.', 'country': 'US'},
    26: {'name': 'Boston Logan International Airport', 'code': 'BOS', 'city': 'Boston', 'country': 'US'},
    27: {'name': 'Fort Lauderdale-Hollywood International Airport', 'code': 'FLL', 'city': 'Fort Lauderdale',
         'country': 'US'},
    28: {'name': 'Cleveland Hopkins International Airport', 'code': 'CLE', 'city': 'Cleveland', 'country': 'US'},
    29: {'name': 'Daniel K. Inouye International Airport', 'code': 'HNL', 'city': 'Honolulu', 'country': 'US'},
    30: {'name': 'Chicago Midway International Airport', 'code': 'MDW', 'city': 'Chicago', 'country': 'US'},
    31: {'name': 'Dallas Love Field', 'code': 'DAL', 'city': 'Dallas', 'country': 'US'},
    32: {'name': 'Indianapolis International Airport', 'code': 'IND', 'city': 'Indianapolis', 'country': 'US'},
    33: {'name': 'St. Louis Lambert International Airport', 'code': 'STL', 'city': 'St. Louis', 'country': 'US'},
    34: {'name': 'Pittsburgh International Airport', 'code': 'PIT', 'city': 'Pittsburgh', 'country': 'US'},
    35: {'name': 'Baltimore-Washington International Airport', 'code': 'BWI', 'city': 'Baltimore', 'country': 'US'},
    36: {'name': 'Salt Lake City International Airport', 'code': 'SLC', 'city': 'Salt Lake City', 'country': 'US'},
    37: {'name': 'San Antonio International Airport', 'code': 'SAT', 'city': 'San Antonio', 'country': 'US'},
    38: {'name': 'Kansas City International Airport', 'code': 'MCI', 'city': 'Kansas City', 'country': 'US'},
    39: {'name': 'Sacramento International Airport', 'code': 'SMF', 'city': 'Sacramento', 'country': 'US'},
    40: {'name': 'Raleigh-Durham International Airport', 'code': 'RDU', 'city': 'Raleigh', 'country': 'US'},
    41: {'name': 'San Jose International Airport', 'code': 'SJC', 'city': 'San Jose', 'country': 'US'},
    42: {'name': 'Nashville International Airport', 'code': 'BNA', 'city': 'Nashville', 'country': 'US'},
    43: {'name': 'Palm Beach International Airport', 'code': 'PBI', 'city': 'West Palm Beach', 'country': 'US'},
    44: {'name': 'Austin-Bergstrom International Airport', 'code': 'AUS', 'city': 'Austin', 'country': 'US'},
    45: {'name': 'El Paso International Airport', 'code': 'ELP', 'city': 'El Paso', 'country': 'US'},
    46: {'name': 'Tucson International Airport', 'code': 'TUS', 'city': 'Tucson', 'country': 'US'},
    47: {'name': 'Richmond International Airport', 'code': 'RIC', 'city': 'Richmond', 'country': 'US'},
    48: {'name': 'Louisville International Airport', 'code': 'SDF', 'city': 'Louisville', 'country': 'US'},
    49: {'name': 'Ontario International Airport', 'code': 'ONT', 'city': 'Ontario', 'country': 'US'},
    50: {'name': 'Albuquerque International Sunport', 'code': 'ABQ', 'city': 'Albuquerque', 'country': 'US'},
    51: {'name': 'Will Rogers World Airport', 'code': 'OKC', 'city': 'Oklahoma City', 'country': 'US'},
    52: {'name': 'Bradley International Airport', 'code': 'BDL', 'city': 'Hartford', 'country': 'US'},
    53: {'name': 'Buffalo Niagara International Airport', 'code': 'BUF', 'city': 'Buffalo', 'country': 'US'},
    54: {'name': 'Ted Stevens Anchorage International Airport', 'code': 'ANC', 'city': 'Anchorage', 'country': 'US'},
    55: {'name': 'Reno-Tahoe International Airport', 'code': 'RNO', 'city': 'Reno', 'country': 'US'},
    56: {'name': 'John Glenn Columbus International Airport', 'code': 'CMH', 'city': 'Columbus', 'country': 'US'},
    57: {'name': 'Piedmont Triad International Airport', 'code': 'GSO', 'city': 'Greensboro', 'country': 'US'},
    58: {'name': 'Spokane International Airport', 'code': 'GEG', 'city': 'Spokane', 'country': 'US'},
    59: {'name': 'Gerald R. Ford International Airport', 'code': 'GRR', 'city': 'Grand Rapids', 'country': 'US'},
    60: {'name': 'Eppley Airfield', 'code': 'OMA', 'city': 'Omaha', 'country': 'US'},
    61: {'name': 'Birmingham-Shuttlesworth International Airport', 'code': 'BHM', 'city': 'Birmingham',
         'country': 'US'},
    62: {'name': 'Jacksonville International Airport', 'code': 'JAX', 'city': 'Jacksonville', 'country': 'US'},
    63: {'name': 'Norfolk International Airport', 'code': 'ORF', 'city': 'Norfolk', 'country': 'US'},
    64: {'name': 'Syracuse Hancock International Airport', 'code': 'SYR', 'city': 'Syracuse', 'country': 'US'},
    65: {'name': 'Cincinnati/Northern Kentucky International Airport', 'code': 'CVG', 'city': 'Cincinnati',
         'country': 'US'},
    66: {'name': 'Boise Airport', 'code': 'BOI', 'city': 'Boise', 'country': 'US'},
    67: {'name': 'Rochester International Airport', 'code': 'ROC', 'city': 'Rochester', 'country': 'US'},
    68: {'name': 'Lubbock Preston Smith International Airport', 'code': 'LBB', 'city': 'Lubbock', 'country': 'US'},
    69: {'name': 'Long Beach Airport', 'code': 'LGB', 'city': 'Long Beach', 'country': 'US'},
    70: {'name': 'Dane County Regional Airport', 'code': 'MSN', 'city': 'Madison', 'country': 'US'},
    71: {'name': 'Tulsa International Airport', 'code': 'TUL', 'city': 'Tulsa', 'country': 'US'},
    72: {'name': 'Pensacola International Airport', 'code': 'PNS', 'city': 'Pensacola', 'country': 'US'},
    73: {'name': 'Des Moines International Airport', 'code': 'DSM', 'city': 'Des Moines', 'country': 'US'},
    74: {'name': 'Southwest Florida International Airport', 'code': 'RSW', 'city': 'Fort Myers', 'country': 'US'},
    75: {'name': 'Charleston International Airport', 'code': 'CHS', 'city': 'Charleston', 'country': 'US'},
    76: {'name': 'Dayton International Airport', 'code': 'DAY', 'city': 'Dayton', 'country': 'US'},
    77: {'name': 'Colorado Springs Airport', 'code': 'COS', 'city': 'Colorado Springs', 'country': 'US'},
    78: {'name': 'Savannah/Hilton Head International Airport', 'code': 'SAV', 'city': 'Savannah', 'country': 'US'},
    79: {'name': 'Little Rock National Airport', 'code': 'LIT', 'city': 'Little Rock', 'country': 'US'},
    80: {'name': 'Myrtle Beach International Airport', 'code': 'MYR', 'city': 'Myrtle Beach', 'country': 'US'},
    81: {'name': 'Palm Springs International Airport', 'code': 'PSP', 'city': 'Palm Springs', 'country': 'US'},
    82: {'name': 'Mobile Regional Airport', 'code': 'MOB', 'city': 'Mobile', 'country': 'US'},
    83: {'name': 'Tallahassee International Airport', 'code': 'TLH', 'city': 'Tallahassee', 'country': 'US'},
    84: {'name': 'Chattanooga Metropolitan Airport', 'code': 'CHA', 'city': 'Chattanooga', 'country': 'US'},
    85: {'name': 'New Orleans Louis Armstrong International Airport', 'code': 'MSY', 'city': 'New Orleans',
         'country': 'US'},
    86: {'name': 'Gainesville Regional Airport', 'code': 'GNV', 'city': 'Gainesville', 'country': 'US'},
    87: {'name': 'Kahului Airport', 'code': 'OGG', 'city': 'Kahului', 'country': 'US'},
    88: {'name': 'Lihue Airport', 'code': 'LIH', 'city': 'Lihue', 'country': 'US'},
    89: {'name': 'Kona International Airport', 'code': 'KOA', 'city': 'Kailua-Kona', 'country': 'US'},
    90: {'name': 'Hilo International Airport', 'code': 'ITO', 'city': 'Hilo', 'country': 'US'},
    91: {'name': 'Fresno Yosemite International Airport', 'code': 'FAT', 'city': 'Fresno', 'country': 'US'},
    92: {'name': 'Burlington International Airport', 'code': 'BTV', 'city': 'Burlington', 'country': 'US'},
    93: {'name': 'Asheville Regional Airport', 'code': 'AVL', 'city': 'Asheville', 'country': 'US'},
    94: {'name': 'Corpus Christi International Airport', 'code': 'CRP', 'city': 'Corpus Christi', 'country': 'US'},
    95: {'name': 'Harrisburg International Airport', 'code': 'MDT', 'city': 'Harrisburg', 'country': 'US'},
    96: {'name': 'Wichita Dwight D. Eisenhower National Airport', 'code': 'ICT', 'city': 'Wichita', 'country': 'US'},
    97: {'name': 'Key West International Airport', 'code': 'EYW', 'city': 'Key West', 'country': 'US'},
    98: {'name': 'Knoxville McGhee Tyson Airport', 'code': 'TYS', 'city': 'Knoxville', 'country': 'US'},
    99: {'name': 'Lexington Blue Grass Airport', 'code': 'LEX', 'city': 'Lexington', 'country': 'US'},
    100: {'name': 'Amarillo Rick Husband International Airport', 'code': 'AMA', 'city': 'Amarillo', 'country': 'US'}
}

airlines_list = ["AA", "UA", "DL", "WN", "AS", "NK", "F9", "G4", "B6", "HA", "SY", "MQ", "YX",
                 "OH", "9E", "OO", "YV", "QX", "CP", "ZW", "AX", "C5", "KS", "EM", "9K", "VX", ]


def create_default_data():
    # Aircraft = apps.get_model('flights', 'Aircraft')
    # Airport = apps.get_model('flights', 'Airport')
    # Seat = apps.get_model('flights', 'Seat')
    # Flight = apps.get_model('flights', 'Flight')
    # Extra = apps.get_model('flights', 'Extra')


    for i in airport_dict.values():
        Airport.objects.create(
            name=i['name'],
            code=i['code'],
            city=i['city'],
            country=i['country']
        )

    Aircraft.objects.create(
        model='Boeing',
        aircraft_type=AircraftTypes.BOEING,
        total_seats=600,
    )

    Aircraft.objects.create(
        model='Airbus A310-200',
        aircraft_type=AircraftTypes.AIRBUS,
        total_seats=466,
    )
    Aircraft.objects.create(
        model='Embraer 190',
        aircraft_type=AircraftTypes.EMBRAER,
        total_seats=106,
    )
    Seat.objects.create(
        row_letter='A',
        seat_number='1',
        seat_type=TextClassType.ECONOMY,
    )
    Seat.objects.create(
        row_letter='B',
        seat_number='1',
        seat_type=TextClassType.ECONOMY,
    )
    Seat.objects.create(
        row_letter='C',
        seat_number=1,
        seat_type=TextClassType.ECONOMY,
    )

    for i in flight_dict.items():
        f = Flight.objects.create(
            name=f'{rn.choice(airlines_list)} {rn.randint(1000, 9999)}',
            departure_time=i[1]['dep_time'],
            arrival_time=i[1]['arr_time'],
            aircraft=Aircraft.objects.get(pk=rn.randint(1, 3)),
            origin_airport=Airport.objects.get(pk=rn.randint(1, 59)),
            destination_airport=Airport.objects.get(pk=rn.randint(1, 59)),
        )
        plane = Aircraft.objects.get(pk=f.aircraft.id)
        if plane.aircraft_type == AircraftTypes.BOEING:
            f.economy_seats = 300
            f.business_seats = 280
            f.first_class_seats = 20
        elif plane.aircraft_type == AircraftTypes.AIRBUS:
            f.economy_seats = 220
            f.business_seats = 220
            f.first_class_seats = 26
        elif plane.aircraft_type == AircraftTypes.EMBRAER:
            f.economy_seats = 50
            f.business_seats = 50
            f.first_class_seats = 6
        else:
            f.economy_seats = 100
            f.business_seats = 40
            f.first_class_seats = 10
        f.save()
        eta = f.departure_time
        task = flight_expiration_task.apply_async(args=[f.id], eta=eta)
        f.task_id = task.id
        f.save()

    Extra.objects.create(
        name='Choice menu',
        description='Possibility to choose dishes from the menu on board',
        available=True,
        price=40.0
    )
    Extra.objects.create(
        name='Wi-Fi',
        description='In-Flight Entertainment',
        available=True,
        price=20.0
    )
    Extra.objects.create(
        name='Extra baggage',
        description='Possibility to take more baggage',
        available=True,
        price=30.0
    )


def create_groups():
    # Создание группы Check In Manager
    check_in_manager_group = Group.objects.create(name='Check In Manager')
    # Назначение разрешений для Check In Manager
    check_in_perm = Permission.objects.get(codename='can_approve_check_in')
    check_in_manager_group.permissions.add(check_in_perm)

    # Создание группы Gate Manager
    gate_manager_group = Group.objects.create(name='Gate Manager')
    # Назначение разрешений для Gate Manager
    onboard_perm = Permission.objects.get(codename='can_approve_onboard')
    gate_manager_group.permissions.add(onboard_perm)

    # Разные другие разрешения
    extra_content_type = ContentType.objects.get_for_model(Extra)
    extra_perm = Permission.objects.get(content_type=extra_content_type, codename='can_manage_extras')
    seat_perm = Permission.objects.get(codename='can_manage_seats')
    flight_perm = Permission.objects.get(codename='can_manage_flights')
    aircraft_perm = Permission.objects.get(codename='can_manage_aircraft')
    airport_perm = Permission.objects.get(codename='can_manage_airports')

    # Создание группы Supervisor
    supervisor_group = Group.objects.create(name='Supervisor')
    # Назначение разрешений для Supervisor
    supervisor_group.permissions.add(check_in_perm, onboard_perm, extra_perm, seat_perm, flight_perm,
                                     aircraft_perm, airport_perm)


# if '__main__' == __name__:
#     create_default_data()
#     create_groups()
