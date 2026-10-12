# Data

This repository does not carry its raw inputs. The files listed below were present locally when the results in the README were produced, and were deleted on 2026-10-12 to reclaim **1.79 GB** of disk. Every one of them is a download from a public upstream source, so nothing unique was lost.

This file exists so that a re-download can be *checked* rather than assumed to match. It records the exact inventory, not just the source.

Upstream sources, with links and licences, are in the README under **Data**.

## What was removed

1.79 GB in 15967 files.

| Path | Size | Files |
|---|---|---|
| `data/hansard` | 1.79 GB | 15531 |
| `data/ngram_cache` | 4.15 MB | 436 |

## Restoring it

`data/hansard` held the UK Hansard XML corpus; `data/ngram_cache` held cached Google Books Ngrams API responses. Both refill from the fetch stages. The tables and figures the README quotes are tracked.

## Inventory

`data_manifest.csv` carries every file with its exact byte length and a fingerprint. Files of 32 MiB or less have a full `sha256`. Larger files have `headtail256`: a sha256 over the first mebibyte, the last mebibyte and the exact byte length, which catches a truncated or altered download without rereading gigabytes.

The 40 largest of 15967 files; `data_manifest.csv` has them all.

| File | Size | Fingerprint |
|---|---|---|
| `data/hansard/parts/1951-06-11.tsv.gz` | 456.18 KB | `sha256:b100f936e85020cab3de4283b52bcbcf72314d184958adde35defcd903995e64` |
| `data/hansard/parts/1984-05-22.tsv.gz` | 424.88 KB | `sha256:35435aeed84ce6a36befdcc926fffa8006bf524ecccaf1b5defe07c61adbc4c4` |
| `data/hansard/parts/1988-06-14.tsv.gz` | 406.15 KB | `sha256:96739e28c0d8d55dc97ee787d8980c3d7ada15d4d7b8a0605207fbc3fa36c812` |
| `data/hansard/parts/1985-03-05.tsv.gz` | 398.91 KB | `sha256:d32f728d3618c3c45f08ddbe55b58f99092a5fb9f9e20f1cab8a604f3caf229f` |
| `data/hansard/parts/2000-01-25.tsv.gz` | 393.55 KB | `sha256:748da09199407a1e91bb1c9875e437cfb57eac1c6d34e9522016ed93e0127b77` |
| `data/hansard/parts/1977-06-21.tsv.gz` | 390.23 KB | `sha256:866a7e859c7498df2f0515b2269be51420f4ab375e68551124e0758f1ae02285` |
| `data/hansard/parts/1987-11-10.tsv.gz` | 383.04 KB | `sha256:a41d26f23e9237fe6d1233754ee4e5eea418c5c1b7414ce02378198c0832603b` |
| `data/hansard/parts/1936-07-22.tsv.gz` | 362.37 KB | `sha256:9d6da50d9b77b593c8809844501c003f9d61112ec9f9856b2624cb75e42c1882` |
| `data/hansard/parts/1986-12-10.tsv.gz` | 354.18 KB | `sha256:fb9fc149ec2e9e572e8a9abc407ef52bdc37f232265dd5c2e0fdd10226fbb764` |
| `data/hansard/parts/1977-07-28.tsv.gz` | 342.22 KB | `sha256:0daa8b71464111475c16844a1202f3dbf729918ee5ec5c8ce4e722f1cd8d57d9` |
| `data/hansard/parts/1978-08-01.tsv.gz` | 340.96 KB | `sha256:a6946e87e6ccf9fb0f9568b2e7ab515386b815d8955747467caad034c5d4a0fa` |
| `data/hansard/parts/1980-08-04.tsv.gz` | 334.95 KB | `sha256:f261162397487658745759f0e6e6cc092aa57aa16825acbdda78210b728c0111` |
| `data/hansard/parts/1984-07-11.tsv.gz` | 331.02 KB | `sha256:e5c3fa59cf7b6ca3c4e7923e8dbcdd5d18c5b12e7db1628437fefcfa0fb2fe10` |
| `data/hansard/parts/1951-06-07.tsv.gz` | 330.75 KB | `sha256:e6823fd07820d2253f245671f742194fc564a095964f45d1c4e87f4729e8ffe3` |
| `data/hansard/parts/1981-04-01.tsv.gz` | 325.02 KB | `sha256:daa7ea5b2c3937a9da83c8c1db0037aadec57038d7a3373a211fdeb9a173243b` |
| `data/hansard/parts/1990-03-13.tsv.gz` | 323.81 KB | `sha256:b5219e8a5e3afb31578feed2299843a3a3e07358f44cc31682cf288848ff5f1c` |
| `data/hansard/parts/1967-07-13.tsv.gz` | 318.41 KB | `sha256:a2efa003bf614ae72993dc8a701f4be228b699cc7587fc14872ca916b68002ef` |
| `data/hansard/parts/1993-03-24.tsv.gz` | 314.83 KB | `sha256:8bb2b656990ca7b2475e1c92a29ffaba2ccf7b5ce5e03bb5156d811f3478de4c` |
| `data/hansard/parts/1967-03-20.tsv.gz` | 312.80 KB | `sha256:ce4f52c19e8d0f267cc8e32e1eeb5fdf6ab3c68395ec60a1ab626fb76b5bde8f` |
| `data/hansard/parts/1965-03-25.tsv.gz` | 311.15 KB | `sha256:02b0fd317ce9582f66a8c5db818bd88223651120fdf49363cba561617607e388` |
| `data/hansard/parts/1968-07-24.tsv.gz` | 308.53 KB | `sha256:0c45a1c81cd4e128025b17125daca089e034dee2421dd9664d370d59c980a38b` |
| `data/hansard/parts/1974-07-29.tsv.gz` | 306.87 KB | `sha256:39aed4ab92a7a290ddf5b00a2f57c0eb6c5f16d7305c848a0230e1fc5ef5568b` |
| `data/hansard/parts/1949-07-25.tsv.gz` | 303.28 KB | `sha256:df59521f70dfcf883e09693838154c8aba617f3e3577833fad4476e3a322274f` |
| `data/hansard/parts/1969-06-12.tsv.gz` | 302.36 KB | `sha256:b4a32bfe02a1c6d9a184ea16f9789a919bf6b881ba9375122e1f3aaeb400b053` |
| `data/hansard/parts/1954-03-11.tsv.gz` | 301.41 KB | `sha256:1c53e815c34f60cf61c740c7a54c8d9d991ab79c6cc6bd50cbc6dc3cb046e5f0` |
| `data/hansard/parts/1965-06-16.tsv.gz` | 296.71 KB | `sha256:55be1fc99c7721b1614998c580c597d37e4db89d16f05cb3d878ae5437e43f50` |
| `data/hansard/parts/1978-12-12.tsv.gz` | 293.03 KB | `sha256:a88208c880deff84c4ecbe2b452fe59ebf4e51295863837f99731ff5a04a7198` |
| `data/hansard/parts/1969-02-25.tsv.gz` | 292.69 KB | `sha256:da84fac496ec8d9cd70d5c595689ebf5a2b835a36558500a9dda9a5f4c7c4c94` |
| `data/hansard/parts/1952-03-26.tsv.gz` | 292.22 KB | `sha256:974e52caadaecd9af1769bcd7cad53b014b1b655961806e6af22e1a0a24a64f0` |
| `data/hansard/parts/1972-07-06.tsv.gz` | 291.42 KB | `sha256:fc38a6685ecbc742396f134f297c3a62e9b40c8d4a1c32314dd874622100a3e4` |
| `data/hansard/parts/1965-08-03.tsv.gz` | 291.02 KB | `sha256:ad7006137f9b8339abcd241b442aa9ab7e683538464c354a580ae5bbbe85e2e8` |
| `data/hansard/parts/1986-12-15.tsv.gz` | 288.01 KB | `sha256:213046eb9eae6f6f143360fa70e453ef933e7a95e377799944541ffd9f181811` |
| `data/hansard/parts/1977-12-14.tsv.gz` | 287.17 KB | `sha256:548a0171db696b570af09162aa2822a406253fa6ecb0a0e61e91bdc6c14a2968` |
| `data/hansard/parts/1976-12-20.tsv.gz` | 286.61 KB | `sha256:82802d98bb10effd20c1c0bf4683a4ae74b74e9a810f8ae043a4c577b17fc95d` |
| `data/hansard/parts/1991-07-22.tsv.gz` | 285.59 KB | `sha256:44ff1fee6448d0d935cd885e886c3d094dab31a5bdda08add0005d86635f02fe` |
| `data/hansard/parts/1969-07-23.tsv.gz` | 285.22 KB | `sha256:b012a3f9927bf81255b282d2552f344c65569d8cd77e404d4621d305d506a7bf` |
| `data/hansard/parts/1990-07-23.tsv.gz` | 284.71 KB | `sha256:407d0080806dd126e95113ad71e0c4d223e25fcf6dde32b17e7347d2076fe200` |
| `data/hansard/parts/1972-03-29.tsv.gz` | 284.27 KB | `sha256:10989fe600160e17e1f1a33bd9efc82228a1cf701962cb4c7479609bf670b37a` |
| `data/hansard/parts/1998-03-09.tsv.gz` | 283.86 KB | `sha256:48d56a087d1f0cbec2ba1e3b7eb3a0b40ee7c55b4103d45f5b393d28f2bc5b13` |
| `data/hansard/parts/1992-12-14.tsv.gz` | 282.53 KB | `sha256:1a714f05c777b9f5c28e80a5214ae76f36ade76d821a269a8cb55c862195b3b2` |

A source that is live rather than a fixed release will not reproduce these fingerprints. Where that applies it is said above.

