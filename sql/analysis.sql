-- Run against the validated `prices` table using SQLite.
-- LAG partitions by ticker so one stock never inherits another stock's price.
WITH lagged AS (
    SELECT Date, Ticker, Close, Volume,
           LAG(Close) OVER (PARTITION BY Ticker ORDER BY Date) AS previous_close
    FROM prices
), daily AS (
    SELECT *, Close / previous_close - 1.0 AS daily_return
    FROM lagged
)
SELECT Ticker,
       SUBSTR(Date, 1, 7) AS Month,
       COUNT(daily_return) AS return_observations,
       AVG(daily_return) AS mean_daily_return,
       MIN(daily_return) AS worst_day,
       MAX(daily_return) AS best_day,
       AVG(Volume) AS mean_daily_volume
FROM daily
GROUP BY Ticker, SUBSTR(Date, 1, 7)
ORDER BY Ticker, Month;
