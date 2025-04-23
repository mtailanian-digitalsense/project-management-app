from sqlalchemy import create_engine, text
import pandas as pd
import calendar

months = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Setiembre', 'Octubre', 'Noviembre', 'Diciembre'
]

team_db_path = "sqlite:///data/team_members.db"
projects_db_path = "sqlite:///data/projects.db"

engine = create_engine(team_db_path)
query = "SELECT * FROM team_members"
team_members = pd.read_sql(query, engine)

engine = create_engine(projects_db_path)
query = "SELECT * FROM projects"
projects = pd.read_sql(query, engine)
projects['Inicio'] = pd.to_datetime(projects['Inicio'])
projects['Fin'] = pd.to_datetime(projects['Fin'])

# How many days from each month are assigned to each project for each team member
assignation_days = projects.join(
    projects.apply(lambda p: pd.Series(pd.date_range(p['Inicio'], p['Fin'], freq='D').to_period('M')), axis=1)
    .apply(lambda x: pd.Series(x).value_counts(), axis=1)
    .fillna(0)
    .astype(int)
)
## Rename columns to Spanish month names
assignation_days.columns = assignation_days.columns.astype(str)
month_mapping = {f'2025-{i+1:02d}': month for i, month in enumerate(months)}
assignation_days.rename(columns=month_mapping, inplace=True)

# Convert to hours
# assignation_hours = assignation_days.copy()
# assignation_days['HorasMes'] = assignation_days['HorasMes'].astype(float)
# assignation_hours[months] = assignation_hours[months].apply(lambda x: x * assignation_days['HorasMes'] / 30, axis=0)

# Convert to hours
assignation_hours = assignation_days.copy()
assignation_days['HorasMes'] = assignation_days['HorasMes'].astype(float)
days_in_month = {month: calendar.monthrange(2025, i + 1)[1] for i, month in enumerate(months)}
for month in months:
    assignation_hours[month] = assignation_days[month] / days_in_month[month] * assignation_days['HorasMes']
assignation_hours[months] = assignation_hours[months].astype(int)

print()

team_members[months] = team_members[months].apply(lambda x: x.astype(int))
available_hours = team_members[months].sum(axis=0)
assigned_hours = assignation_hours[months].sum(axis=0)
metric = assigned_hours / available_hours * 100
metric = metric.to_frame(name='% Asignación').T