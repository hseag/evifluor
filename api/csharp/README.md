# eviFluor Duo C# Interface

This directory contains the C# interface for the eviFluor Duo Fluorometer.
It is intended for .NET applications that need either a guided measurement workflow or direct low-level device control.

## Quick Start

- Main documentation: [C# Interfaces](../../doc/csharp.md)
- High-level API: [C# High-Level API](../../doc/csharp-high-level.md)
- Low-level API: [C# Low-Level API](../../doc/csharp-low-level.md)
- Package availability: NuGet package `Hseagcom.EviFluor`

## What You Get

The C# package supports two integration styles:

- a high-level API built around `Run` for standard workflows
- a low-level API built around `Device` for custom control

This makes the C# interface suitable for:

- liquid handler integrations
- lab automation software
- custom desktop or service applications
- workflows that need persisted measurement state
