----------------- Drivers by wins in the 2___ year --------------


CREATE OR REPLACE VIEW "DriverWins2023View" AS
WITH DriverWinsRanked AS (
    SELECT
        "dd"."driverRef" AS "driver_reference",
        "dd"."forename" AS "driver_forename",
        "dd"."surname" AS "driver_surname",
        "dd"."dob" AS "driver_dob",
        "dd"."nationality" AS "driver_nationality",
        "dd"."code" AS "driver_code",
        "ds"."wins" AS "wins_in_2023",
        ROW_NUMBER() OVER(PARTITION BY "dd"."driverRef" ORDER BY "ds"."wins" DESC) AS "win_rank"
    FROM
        "driverDim" "dd"
    JOIN
        "driverStandingsDim" "ds" ON "dd"."driverId" = "ds"."driverId"
    JOIN
        "raceResultsFact" "rf" ON "ds"."driverStandingsId" = "rf"."driverStandingsId"
    JOIN
        "raceDim" "rd" ON "rf"."raceId" = "rd"."raceId"
    WHERE
        EXTRACT(YEAR FROM "rd"."date") = 2023  -- Filter for races in year ____
)
SELECT
    "driver_reference",
    "driver_forename",
    "driver_surname",
    "driver_dob",
    "driver_nationality",
    "driver_code",
    "wins_in_2023"
FROM
    DriverWinsRanked
WHERE
    "win_rank" = 1  -- Select only the top-ranked rows (maximum wins for each driver)
ORDER BY
    "wins_in_2023" DESC;  -- Order by wins in descending order


----------------------- Constructor wins by year ----------------------------------------------------------------------


CREATE OR REPLACE VIEW "ConstructorWins2024View" AS
WITH ConstructorWinsRanked AS (
    SELECT
        "cd"."constructorRef" AS "constructor_reference",
        "cd"."name" AS "constructor_name",
        "cd"."nationality_constructors" AS "constructor_nationality",
        "cs"."wins_constructorstandings" AS "wins_in_2024",
        ROW_NUMBER() OVER(PARTITION BY "cd"."constructorRef" ORDER BY "cs"."wins_constructorstandings" DESC) AS "win_rank"
    FROM
        "constructorDim" "cd"
    JOIN
        "constructorStandingsDim" "cs" ON "cd"."constructorId" = "cs"."constructorId"
    JOIN
        "raceResultsFact" "rf" ON "cs"."constructorStandingsId" = "rf"."constructorStandingsId"
    JOIN
        "raceDim" "rd" ON "rf"."raceId" = "rd"."raceId"
    WHERE
        EXTRACT(YEAR FROM "rd"."date") = 2024  -- Filter for races in the year 2024
)
SELECT
    "constructor_reference",
    "constructor_name",
    "constructor_nationality",
    "wins_in_2024"
FROM
    ConstructorWinsRanked
WHERE
    "win_rank" = 1  -- Select only the top-ranked rows (maximum wins for each constructor)
ORDER BY
    "wins_in_2024" DESC;  -- Order by wins in descending order



----------------------- Driver performance by circuit -----------------------------------------------------------

	
	
CREATE OR REPLACE VIEW "DriverPerformanceByCircuitView" AS
SELECT
    "dd"."driverRef" AS "driver_reference",
    "dd"."forename" AS "driver_forename",
    "dd"."surname" AS "driver_surname",
    "cd"."circuitId" AS "circuit_id",
    "cd"."name_y" AS "circuit_name",
    "cd"."country" AS "circuit_country",
    AVG("rf"."positionOrder") AS "avg_finish_position",
    COUNT("rf"."resultId") AS "races_count",
    SUM("rf"."points") AS "total_points",
    MAX("rf"."positionOrder") AS "best_finish_position",
    MIN("rf"."positionOrder") AS "worst_finish_position"
FROM
    "driverDim" "dd"
JOIN
    "raceResultsFact" "rf" ON "dd"."driverId" = "rf"."driverId"
JOIN
    "raceDim" "rd" ON "rf"."raceId" = "rd"."raceId"
JOIN
    "circuitDim" "cd" ON "rd"."circuitId" = "cd"."circuitId"
GROUP BY
    "dd"."driverRef", "dd"."forename", "dd"."surname", "cd"."circuitId", "cd"."name_y", "cd"."country"
ORDER BY
    "dd"."driverRef", "cd"."name_y";



----------------------- Construtor perfomance by season ------------------------------------------------------------


CREATE OR REPLACE VIEW "ConstructorPerformanceOverSeasonsView" AS
SELECT
    "cd"."constructorRef" AS "constructor_reference",
    "cd"."name" AS "constructor_name",
    "rd"."year" AS "season_year",
    SUM("rf"."points") AS "total_points",
    COUNT("rf"."resultId") AS "races_count",
    COUNT(DISTINCT "rd"."raceId") AS "races_entered",
    SUM(CASE WHEN "rf"."positionOrder" = 1 THEN 1 ELSE 0 END) AS "wins",
    SUM(CASE WHEN "rf"."positionOrder" <= 3 THEN 1 ELSE 0 END) AS "podiums"
FROM
    "constructorDim" "cd"
JOIN
    "raceResultsFact" "rf" ON "cd"."constructorId" = "rf"."constructorId"
JOIN
    "raceDim" "rd" ON "rf"."raceId" = "rd"."raceId"
GROUP BY
    "cd"."constructorRef", "cd"."name", "rd"."year"
ORDER BY
    "cd"."constructorRef", "rd"."year";
	
	
----------------------- Driver perfomance trends ---------------------------------------------------------------


CREATE OR REPLACE VIEW "DriverPerformanceTrendsView" AS
SELECT
    "dd"."driverRef" AS "driver_reference",
    "dd"."forename" AS "driver_forename",
    "dd"."surname" AS "driver_surname",
    "rd"."year" AS "season_year",
    AVG("rf"."positionOrder") AS "avg_finish_position",
    SUM("rf"."points") AS "total_points",
    COUNT("rf"."resultId") AS "races_count",
    SUM(CASE WHEN "rf"."positionOrder" = 1 THEN 1 ELSE 0 END) AS "wins",
    SUM(CASE WHEN "rf"."positionOrder" <= 3 THEN 1 ELSE 0 END) AS "podiums"
FROM
    "driverDim" "dd"
JOIN
    "raceResultsFact" "rf" ON "dd"."driverId" = "rf"."driverId"
JOIN
    "raceDim" "rd" ON "rf"."raceId" = "rd"."raceId"
GROUP BY
    "dd"."driverRef", "dd"."forename", "dd"."surname", "rd"."year"
ORDER BY
    "dd"."driverRef", "rd"."year";



----------------------- Circuit records ----------------------------------------------------------------------


CREATE OR REPLACE VIEW "CircuitRecordsView" AS
SELECT
    "cd"."name_y" AS "circuit_name",
    "rd"."year" AS "season_year",
    "dd"."driverRef" AS "driver_reference",
    "dd"."forename" AS "driver_forename",
    "dd"."surname" AS "driver_surname",
    "rf"."fastestLapTime" AS "fastest_lap_time",
    "rf"."fastestLapSpeed" AS "fastest_lap_speed"
FROM
    "raceResultsFact" "rf"
JOIN
    "raceDim" "rd" ON "rf"."raceId" = "rd"."raceId"
JOIN
    "circuitDim" "cd" ON "rd"."circuitId" = "cd"."circuitId"
JOIN
    "driverDim" "dd" ON "rf"."driverId" = "dd"."driverId"
WHERE
    "rf"."fastestLapTime" IS NOT NULL
ORDER BY
    "cd"."name_y", "rd"."year", "rf"."fastestLapTime";
	


----------------------- Pit stop effectivness ----------------------------------------------------------------------



CREATE OR REPLACE VIEW "PitStopEffectivenessView" AS
SELECT
    "rd"."year" AS "season_year",
    "cd"."name" AS "constructor_name",
    "dd"."driverRef" AS "driver_reference",
    "dd"."forename" AS "driver_forename",
    "dd"."surname" AS "driver_surname",
    "rf"."positionOrder" AS "finish_position",
    COUNT("ps"."stop") AS "pit_stops_count",
    AVG("ps"."duration") AS "avg_pit_stop_duration"
FROM
    "pitStopsDim" "ps"
JOIN
    "raceResultsFact" "rf" ON "ps"."raceId" = "rf"."raceId" AND "ps"."driverId" = "rf"."driverId"
JOIN
    "driverDim" "dd" ON "ps"."driverId" = "dd"."driverId"
JOIN
    "constructorDim" "cd" ON "rf"."constructorId" = "cd"."constructorId"
JOIN
    "raceDim" "rd" ON "rf"."raceId" = "rd"."raceId"
GROUP BY
    "rd"."year", "cd"."name", "dd"."driverRef", "dd"."forename", "dd"."surname", "rf"."positionOrder"
ORDER BY
    "rd"."year", "cd"."name", "dd"."driverRef";


----------------------- Driver winning and podium streaks ----------------------------------------------------------------------


CREATE OR REPLACE VIEW "DriverWinningPodiumStreaksView" AS
WITH RankedResults AS (
    SELECT
        "dd"."driverRef" AS "driver_reference",
        "dd"."forename" AS "driver_forename",
        "dd"."surname" AS "driver_surname",
        "rd"."year" AS "season_year",
        "rd"."date" AS "race_date",
        "rf"."positionOrder" AS "finish_position",
        ROW_NUMBER() OVER (PARTITION BY "dd"."driverRef" ORDER BY "rd"."date") - 
        ROW_NUMBER() OVER (PARTITION BY "dd"."driverRef", "rf"."positionOrder" <= 3 ORDER BY "rd"."date") AS "podium_streak",
        ROW_NUMBER() OVER (PARTITION BY "dd"."driverRef" ORDER BY "rd"."date") - 
        ROW_NUMBER() OVER (PARTITION BY "dd"."driverRef", "rf"."positionOrder" = 1 ORDER BY "rd"."date") AS "win_streak"
    FROM
        "driverDim" "dd"
    JOIN
        "raceResultsFact" "rf" ON "dd"."driverId" = "rf"."driverId"
    JOIN
        "raceDim" "rd" ON "rf"."raceId" = "rd"."raceId"
),
PodiumStreaks AS (
    SELECT
        "driver_reference",
        "driver_forename",
        "driver_surname",
        COUNT(*) AS "streak_length",
        "podium_streak"
    FROM
        RankedResults
    WHERE
        "finish_position" <= 3
    GROUP BY
        "driver_reference", "driver_forename", "driver_surname", "podium_streak"
),
WinningStreaks AS (
    SELECT
        "driver_reference",
        "driver_forename",
        "driver_surname",
        COUNT(*) AS "streak_length",
        "win_streak"
    FROM
        RankedResults
    WHERE
        "finish_position" = 1
    GROUP BY
        "driver_reference", "driver_forename", "driver_surname", "win_streak"
)
SELECT
    "ps"."driver_reference",
    "ps"."driver_forename",
    "ps"."driver_surname",
    MAX("ps"."streak_length") AS "longest_podium_streak",
    COALESCE(MAX("ws"."streak_length"), 0) AS "longest_winning_streak"
FROM
    PodiumStreaks ps
LEFT JOIN
    WinningStreaks ws ON ps."driver_reference" = ws."driver_reference" AND ps."driver_forename" = ws."driver_forename" AND ps."driver_surname" = ws."driver_surname"
GROUP BY
    ps."driver_reference", ps."driver_forename", ps."driver_surname"
ORDER BY
    "longest_podium_streak" DESC, "longest_winning_streak" DESC;



----------------------- Constructor winning and podium streaks ---------------------------------------------------------------


CREATE OR REPLACE VIEW "ConstructorWinningPodiumStreaksView" AS
WITH RankedResults AS (
    SELECT
        "cd"."constructorRef" AS "constructor_reference",
        "cd"."name" AS "constructor_name",
        "rd"."year" AS "season_year",
        "rd"."date" AS "race_date",
        "rf"."positionOrder" AS "finish_position",
        ROW_NUMBER() OVER (PARTITION BY "cd"."constructorRef" ORDER BY "rd"."date") - 
        ROW_NUMBER() OVER (PARTITION BY "cd"."constructorRef", "rf"."positionOrder" <= 3 ORDER BY "rd"."date") AS "podium_streak",
        ROW_NUMBER() OVER (PARTITION BY "cd"."constructorRef" ORDER BY "rd"."date") - 
        ROW_NUMBER() OVER (PARTITION BY "cd"."constructorRef", "rf"."positionOrder" = 1 ORDER BY "rd"."date") AS "win_streak"
    FROM
        "constructorDim" "cd"
    JOIN
        "raceResultsFact" "rf" ON "cd"."constructorId" = "rf"."constructorId"
    JOIN
        "raceDim" "rd" ON "rf"."raceId" = "rd"."raceId"
),
PodiumStreaks AS (
    SELECT
        "constructor_reference",
        "constructor_name",
        COUNT(*) AS "streak_length",
        "podium_streak"
    FROM
        RankedResults
    WHERE
        "finish_position" <= 3
    GROUP BY
        "constructor_reference", "constructor_name", "podium_streak"
),
WinningStreaks AS (
    SELECT
        "constructor_reference",
        "constructor_name",
        COUNT(*) AS "streak_length",
        "win_streak"
    FROM
        RankedResults
    WHERE
        "finish_position" = 1
    GROUP BY
        "constructor_reference", "constructor_name", "win_streak"
)
SELECT
    "ps"."constructor_reference",
    "ps"."constructor_name",
    MAX("ps"."streak_length") AS "longest_podium_streak",
    COALESCE(MAX("ws"."streak_length"), 0) AS "longest_winning_streak"
FROM
    PodiumStreaks ps
LEFT JOIN
    WinningStreaks ws ON ps."constructor_reference" = ws."constructor_reference" AND ps."constructor_name" = ws."constructor_name"
GROUP BY
    ps."constructor_reference", ps."constructor_name"
ORDER BY
    "longest_podium_streak" DESC, "longest_winning_streak" DESC;


----------------------- Constructor seasonal comparison ----------------------------------------------------------------


CREATE OR REPLACE VIEW "ConstructorSeasonalComparisonsView" AS
SELECT
    "cd"."constructorRef" AS "constructor_reference",
    "cd"."name" AS "constructor_name",
    "rd"."year" AS "season_year",
    AVG("rf"."positionOrder") AS "avg_finish_position",
    SUM("rf"."points") AS "total_points",
    COUNT("rf"."resultId") AS "races_count",
    SUM(CASE WHEN "rf"."positionOrder" = 1 THEN 1 ELSE 0 END) AS "wins",
    SUM(CASE WHEN "rf"."positionOrder" <= 3 THEN 1 ELSE 0 END) AS "podiums"
FROM
    "constructorDim" "cd"
JOIN
    "raceResultsFact" "rf" ON "cd"."constructorId" = "rf"."constructorId"
JOIN
    "raceDim" "rd" ON "rf"."raceId" = "rd"."raceId"
GROUP BY
    "cd"."constructorRef", "cd"."name", "rd"."year"
ORDER BY
    "cd"."constructorRef", "rd"."year";
	

----------------------- Driver seasonal comparison ----------------------------------------------------------------------


CREATE OR REPLACE VIEW "DriverSeasonalComparisonsView" AS
SELECT
    "dd"."driverRef" AS "driver_reference",
    "dd"."forename" AS "driver_forename",
    "dd"."surname" AS "driver_surname",
    "rd"."year" AS "season_year",
    AVG("rf"."positionOrder") AS "avg_finish_position",
    SUM("rf"."points") AS "total_points",
    COUNT("rf"."resultId") AS "races_count",
    SUM(CASE WHEN "rf"."positionOrder" = 1 THEN 1 ELSE 0 END) AS "wins",
    SUM(CASE WHEN "rf"."positionOrder" <= 3 THEN 1 ELSE 0 END) AS "podiums"
FROM
    "driverDim" "dd"
JOIN
    "raceResultsFact" "rf" ON "dd"."driverId" = "rf"."driverId"
JOIN
    "raceDim" "rd" ON "rf"."raceId" = "rd"."raceId"
GROUP BY
    "dd"."driverRef", "dd"."forename", "dd"."surname", "rd"."year"
ORDER BY
    "dd"."driverRef", "rd"."year";
	
	
----------------------- Qualifications performance ----------------------------------------------------------------------

	

CREATE OR REPLACE VIEW "DriverQualificationPerformanceView" AS
SELECT
    "dd"."driverRef" AS "driver_reference",
    "dd"."forename" AS "driver_forename",
    "dd"."surname" AS "driver_surname",
    AVG("qd"."quali_time") AS "avg_qualifying_time",
    COUNT(CASE WHEN "qd"."quali_time" IS NOT NULL AND "qd"."quali_time" = '00:00:00' THEN 1 ELSE NULL END) AS "pole_positions"
FROM
    "driverDim" "dd"
JOIN
    "qualificationsDim" "qd" ON "dd"."driverId" = "qd"."driverId"
GROUP BY
    "dd"."driverRef", "dd"."forename", "dd"."surname"
ORDER BY
    "avg_qualifying_time";


----------------------- Driver seasonal performance ----------------------------------------------------------



CREATE OR REPLACE VIEW "DriverSeasonalPerformanceView" AS
SELECT
    "dd"."driverRef" AS "driver_reference",
    "dd"."forename" AS "driver_forename",
    "dd"."surname" AS "driver_surname",
    "rd"."year" AS "season_year",
    SUM("rf"."points") AS "total_points",
    SUM(CASE WHEN "rf"."positionOrder" = 1 THEN 1 ELSE 0 END) AS "wins",
    AVG("rf"."positionOrder") AS "avg_finish_position"
FROM
    "driverDim" "dd"
JOIN
    "raceResultsFact" "rf" ON "dd"."driverId" = "rf"."driverId"
JOIN
    "raceDim" "rd" ON "rf"."raceId" = "rd"."raceId"
GROUP BY
    "dd"."driverRef", "dd"."forename", "dd"."surname", "rd"."year"
ORDER BY
    "dd"."driverRef", "season_year";



----------------------- Constructor seasonal performance --------------------------------------------------------


CREATE OR REPLACE VIEW "ConstructorSeasonalPerformanceView" AS
SELECT
    "cd"."constructorRef" AS "constructor_reference",
    "cd"."name" AS "constructor_name",
    "rd"."year" AS "season_year",
    SUM("rf"."points") AS "total_points",
    SUM(CASE WHEN "rf"."positionOrder" = 1 THEN 1 ELSE 0 END) AS "wins",
    AVG("rf"."positionOrder") AS "avg_finish_position"
FROM
    "constructorDim" "cd"
JOIN
    "raceResultsFact" "rf" ON "cd"."constructorId" = "rf"."constructorId"
JOIN
    "raceDim" "rd" ON "rf"."raceId" = "rd"."raceId"
GROUP BY
    "cd"."constructorRef", "cd"."name", "rd"."year"
ORDER BY
    "cd"."constructorRef", "season_year";


----------------------- Driver performance without Max Verstappen ----------------------------------------------------------


CREATE OR REPLACE VIEW "DriverPerformanceWithoutMaxView" AS
SELECT
    dd."driverRef" AS "driver_reference",
    dd."forename" AS "driver_forename",
    dd."surname" AS "driver_surname",
    AVG(rf."positionOrder") AS "avg_finish_position",
    SUM(rf."points") AS "total_points",
    COUNT(CASE WHEN rf."positionOrder" = 1 THEN 1 ELSE NULL END) AS "wins_count"
FROM
    "driverDim" dd
JOIN
    "raceResultsFact" rf ON dd."driverId" = rf."driverId"
WHERE
    dd."driverRef" <> 'max_verstappen'
GROUP BY
    dd."driverRef", dd."forename", dd."surname"
ORDER BY
    dd."driverRef";


----------------------- Driver performance with Max Verstappen ----------------------------------------------------------


CREATE OR REPLACE VIEW "DriverPerformanceWithMaxView" AS
SELECT
    dd."driverRef" AS "driver_reference",
    dd."forename" AS "driver_forename",
    dd."surname" AS "driver_surname",
    AVG(rf."positionOrder") AS "avg_finish_position",
    SUM(rf."points") AS "total_points",
    COUNT(CASE WHEN rf."positionOrder" = 1 THEN 1 ELSE NULL END) AS "wins_count"
FROM
    "driverDim" dd
JOIN
    "raceResultsFact" rf ON dd."driverId" = rf."driverId"
WHERE
    dd."driverRef" = 'max_verstappen'
GROUP BY
    dd."driverRef", dd."forename", dd."surname"
ORDER BY
    dd."driverRef";


----------------------- Driver most wins in a season ----------------------------------------------------------------------


CREATE OR REPLACE VIEW "DriverMostWinsInSeasonView" AS
SELECT
    dd."driverRef" AS "driver_reference",
    dd."forename" AS "driver_forename",
    dd."surname" AS "driver_surname",
    rd."year" AS "season_year",
    COUNT(CASE WHEN rf."positionOrder" = 1 THEN 1 ELSE NULL END) AS "wins_count"
FROM
    "driverDim" dd
JOIN
    "raceResultsFact" rf ON dd."driverId" = rf."driverId"
JOIN
    "raceDim" rd ON rf."raceId" = rd."raceId"
GROUP BY
    dd."driverRef", dd."forename", dd."surname", rd."year"
ORDER BY
    wins_count DESC
LIMIT 1;


----------------------- Driver most wins in a season excluding Max Verstappen -------------------------------------------------------


CREATE OR REPLACE VIEW "DriverMostWinsInSeasonWithoutMaxView" AS
SELECT
    dd."driverRef" AS "driver_reference",
    dd."forename" AS "driver_forename",
    dd."surname" AS "driver_surname",
    rd."year" AS "season_year",
    COUNT(CASE WHEN rf."positionOrder" = 1 THEN 1 ELSE NULL END) AS "wins_count"
FROM
    "driverDim" dd
JOIN
    "raceResultsFact" rf ON dd."driverId" = rf."driverId"
JOIN
    "raceDim" rd ON rf."raceId" = rd."raceId"
WHERE
    dd."driverRef" <> 'max_verstappen'
GROUP BY
    dd."driverRef", dd."forename", dd."surname", rd."year"
ORDER BY
    wins_count DESC
LIMIT 1;


----------------------- Driver with most wins in a row ----------------------------------------------------------------------


CREATE OR REPLACE VIEW "DriverMostWinsInRowView" AS
WITH ConsecutiveWins AS (
    SELECT
        dd."driverRef",
        dd."forename",
        dd."surname",
        rd."year",
        rf."positionOrder",
        rf."raceId",
        rf."driverId",
        ROW_NUMBER() OVER (PARTITION BY dd."driverRef" ORDER BY rd."date") -
        ROW_NUMBER() OVER (PARTITION BY dd."driverRef", rf."positionOrder" ORDER BY rd."date") AS grp
    FROM
        "driverDim" dd
    JOIN
        "raceResultsFact" rf ON dd."driverId" = rf."driverId"
    JOIN
        "raceDim" rd ON rf."raceId" = rd."raceId"
    WHERE
        rf."positionOrder" = 1
)
SELECT
    "driverRef" AS "driver_reference",
    "forename" AS "driver_forename",
    "surname" AS "driver_surname",
    COUNT(*) AS "wins_in_a_row"
FROM
    ConsecutiveWins
GROUP BY
    "driverRef", "forename", "surname", grp
ORDER BY
    "wins_in_a_row" DESC
LIMIT 1;


----------------------- Driver with most podiums in a season ----------------------------------------------------------------------


CREATE OR REPLACE VIEW "DriverMostPodiumsInSeasonView" AS
SELECT
    dd."driverRef" AS "driver_reference",
    dd."forename" AS "driver_forename",
    dd."surname" AS "driver_surname",
    rd."year" AS "season_year",
    COUNT(CASE WHEN rf."positionOrder" <= 3 THEN 1 ELSE NULL END) AS "podiums_count"
FROM
    "driverDim" dd
JOIN
    "raceResultsFact" rf ON dd."driverId" = rf."driverId"
JOIN
    "raceDim" rd ON rf."raceId" = rd."raceId"
GROUP BY
    dd."driverRef", dd."forename", dd."surname", rd."year"
ORDER BY
    podiums_count DESC
LIMIT 1;


----------------------- Driver with most podiums in a season excluding Max Verstappen ------------------------------------------------------------


CREATE OR REPLACE VIEW "DriverMostPodiumsInSeasonWithoutMaxView" AS
SELECT
    dd."driverRef" AS "driver_reference",
    dd."forename" AS "driver_forename",
    dd."surname" AS "driver_surname",
    rd."year" AS "season_year",
    COUNT(CASE WHEN rf."positionOrder" <= 3 THEN 1 ELSE NULL END) AS "podiums_count"
FROM
    "driverDim" dd
JOIN
    "raceResultsFact" rf ON dd."driverId" = rf."driverId"
JOIN
    "raceDim" rd ON rf."raceId" = rd."raceId"
WHERE
    dd."driverRef" <> 'max_verstappen'
GROUP BY
    dd."driverRef", dd."forename", dd."surname", rd."year"
ORDER BY
    podiums_count DESC
LIMIT 1;


----------------------- Driver with most points in a season  ----------------------------------------------------------------------


CREATE OR REPLACE VIEW "DriverMostPointsInSeasonView" AS
SELECT
    dd."driverRef" AS "driver_reference",
    dd."forename" AS "driver_forename",
    dd."surname" AS "driver_surname",
    rd."year" AS "season_year",
    SUM(rf."points") AS "total_points"
FROM
    "driverDim" dd
JOIN
    "raceResultsFact" rf ON dd."driverId" = rf."driverId"
JOIN
    "raceDim" rd ON rf."raceId" = rd."raceId"
GROUP BY
    dd."driverRef", dd."forename", dd."surname", rd."year"
ORDER BY
    total_points DESC
LIMIT 1;


----------------------- Driver with most points in a season excluding Max Verstappen ----------------------------------------------------------------------


CREATE OR REPLACE VIEW "DriverMostPointsInSeasonWithoutMaxView" AS
SELECT
    dd."driverRef" AS "driver_reference",
    dd."forename" AS "driver_forename",
    dd."surname" AS "driver_surname",
    rd."year" AS "season_year",
    SUM(rf."points") AS "total_points"
FROM
    "driverDim" dd
JOIN
    "raceResultsFact" rf ON dd."driverId" = rf."driverId"
JOIN
    "raceDim" rd ON rf."raceId" = rd."raceId"
WHERE
    dd."driverRef" <> 'max_verstappen'
GROUP BY
    dd."driverRef", dd."forename", dd."surname", rd."year"
ORDER BY
    total_points DESC
LIMIT 1;

