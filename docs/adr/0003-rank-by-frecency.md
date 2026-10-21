# 3. Rank apps by how often and how recently they're opened

**Status:** Accepted  
**Date:** 2026-10-19

## Context

Alphabetical lists make the apps you use most as hard to reach as the ones you never use.

## Decision

An empty search shows the six most-used apps first. Every match's fuzzy score gets a bonus from its launch count (capped), and launches are stored per app in Vyom's state directory.

## Consequences

- The apps you use rise to the top after a few days.
- State is local and per user; nothing leaves the machine.
