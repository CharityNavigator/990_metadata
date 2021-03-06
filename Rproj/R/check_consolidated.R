library(tidyverse)

# Raw output from May 2017 datathon
datathon_raw <- read_csv("data/Concatenated.csv")
datathon_raw %>%
  filter(is.na(VARIABLE_NAME))

datathon <- datathon_raw %>%
  rename(FLAG = `FLAG FOR REVIEW (X)`) %>%
  rename(REQUIRED = `REQUIRED(X)`) %>%
  mutate(FLAG = !is.na(FLAG)) %>%
  mutate(REQUIRED = !is.na(REQUIRED) & REQUIRED %in% c("X", "x", "1")) %>%
  mutate(VARIABLE_NAME = stringr::str_replace_all(VARIABLE_NAME, " ", ""))

# XPaths that occur more than once
repeats <- datathon %>%
  group_by(XPATH, VARIABLE_NAME, DESCRIPTION, LOCATION, Analyst) %>%
  summarise() %>%
  ungroup() %>%
  group_by(XPATH) %>%
  summarise(n = n()) %>%
  ungroup() %>%
  filter(n > 1) %>%
  left_join(datathon, by = "XPATH")

write_csv(repeats, "dt_output/repeats.csv", na="")

# Complete record of attested Xpaths
xpath_master <- read_csv("output/master_file.csv")

# XPaths from the 990 and EZ that were not processed
missing <- anti_join(xpath_master, datathon, by = c("Xpath" = "XPATH")) %>%
  filter(stringr::str_detect(Xpath, "IRS990(EZ)?/")) %>%
  gather(version, count, -c(Versions, Xpath, Source, Type, Description, Line, MinOccur, MaxOccur)) %>%
  filter(!is.na(count)) %>%
  filter(count > 0) %>%
  mutate(year = version %>% substr(1, 4) %>% as.integer) %>%
  group_by(Xpath) %>%
  summarise(max_year = max(year), tot_obs = sum(count)) %>%
  ungroup() %>%
  filter(max_year > 2008) %>%
  filter(tot_obs >= 100) %>%
  left_join(xpath_master, by = "Xpath")

write_csv(missing, "dt_output/missing.csv", na="")

# Too many/few dashes in name -- doesn't happen
misdashed <- datathon %>%
  mutate(dashes = stringr::str_count(VARIABLE_NAME, "-")) %>%
  filter(dashes != 3)

# Identify suffixes used for more than one variable name
repeat_suffix <- datathon %>%
  mutate(dummy = VARIABLE_NAME) %>%
  separate(dummy, into = c("SECTION", "FORM", "LINE", "SUFFIX"), sep = "-") %>%
  group_by(SUFFIX, VARIABLE_NAME) %>%
  mutate(NUM_VARIABLE = n()) %>%
  ungroup() %>%
  group_by(SUFFIX) %>%
  mutate(NUM_SUFFIX = n()) %>%
  select(c(SUFFIX, VARIABLE_NAME, NUM_VARIABLE, NUM_SUFFIX)) %>%
  filter(NUM_VARIABLE != NUM_SUFFIX) %>%
  left_join(datathon, by = "VARIABLE_NAME")

write_csv(repeat_suffix, "dt_output/repeat_suffix.csv", na="")

# Flagged for follow up
flagged <- datathon %>%
  filter(FLAG)

write_csv(repeat_suffix, "dt_output/flagged.csv", na="")

# Cleaned up versin of repeats.csv, above, as reviewed by Kevin Doyle and 
# David Borenstein (Charity Navigator)

repeats_clean <- read_csv("./data/repeats_resolved.csv") %>%
  select(-c(n, `Kevin's Notes`))


dt_rp_resolved <- datathon %>%
  filter(!(XPATH %in% repeats_clean$XPATH)) %>%
  bind_rows(repeats_clean)

# Additional/corrected mapped Xpaths by Kevin Doyle
kd_missing <- read_csv("./data/kevin_missing.csv") %>%
  mutate(Analyst = "Doyle") %>%
  rename(FLAG = `FLAG FOR REVIEW (X)`) %>%
  rename(REQUIRED = `REQUIRED(X)`) %>%
  mutate(FLAG = !is.na(FLAG)) %>%
  mutate(REQUIRED = !is.na(REQUIRED) & REQUIRED %in% c("X", "x", "1"))

# Remove any Xpaths that Kevin corrected and then append to dataset
dt_rp_kd <- dt_rp_resolved %>%
  filter(!(XPATH %in% kd_missing$XPATH)) %>%
  bind_rows(kd_missing)

# Add Schedule N (from Nathan Dietz and Matthew Lee)
sched_n <- read_csv("./data/sched_n.csv") %>%
  mutate(Analyst = "Lee & Dietz") %>%
  rename(FLAG = `FLAG FOR REVIEW (X)`) %>%
  rename(REQUIRED = `REQUIRED(X)`) %>%
  mutate(FLAG = !is.na(FLAG)) %>%
  mutate(REQUIRED = !is.na(REQUIRED) & REQUIRED %in% c("X", "x", "1"))

dt_rp_kd_n <- dt_rp_kd %>%
  filter(!(XPATH %in% sched_n$XPATH)) %>%
  bind_rows(sched_n)

write_csv(dt_rp_kd, "./output/concordance_latest.csv", na = "")

# What's still missing?
still_missing <- anti_join(xpath_master, dt_rp_kd, by = c("Xpath" = "XPATH")) %>%
  filter(stringr::str_detect(Xpath, "IRS990(EZ)?/")) %>%
  gather(version, count, -c(Versions, Xpath, Source, Type, Description, Line, MinOccur, MaxOccur)) %>%
  filter(!is.na(count)) %>%
  filter(count > 0) %>%
  mutate(year = version %>% substr(1, 4) %>% as.integer) %>%
  group_by(Xpath) %>%
  summarise(max_year = max(year), tot_obs = sum(count)) %>%
  ungroup() %>%
  filter(max_year > 2008) %>%
  filter(tot_obs >= 100) %>%
  left_join(xpath_master, by = "Xpath")

write_csv(still_missing, "./output/still_missing.csv", na="")

# Summarize extant variables
dt_rp_kd_n %>%
  select(variable = VARIABLE_NAME, 
         description = DESCRIPTION, 
         location = LOCATION,
         required = REQUIRED,
         notes    = NOTES,
         analyst  = Analyst) %>%
  distinct() %>%
  arrange(variable) %>%
  write_csv("./output/variables.csv", na = "")