# Running the code you are auditing

A source-code finding is only reportable once something executes it. This is the short path from a clone to a
program that prints the wrong behaviour, including when the host has no compiler.

## Option 1 — build the library

Easiest on Windows with no admin rights:

```bash
pip install cmake                          # no admin needed, lands in the Python Scripts dir
# WinLibs portable MinGW-w64: download the .zip release, not the installer
# https://github.com/brechtsanders/winlibs_mingw/releases  (x86_64, UCRT)
unzip winlibs-*.zip -d <workspace>/toolchain
export PATH="<workspace>/toolchain/mingw64/bin:$PATH"
gcc --version && g++ --version

cmake -S . -B build -G "MinGW Makefiles" -DCMAKE_BUILD_TYPE=Release
cmake --build build -j4
```

Write the working `PATH` line into `toolchain/env.sh` and pass that path to every child that needs to compile.
Children must not each rediscover the toolchain.

## When sanitizers are unavailable

MinGW has no working ASan. Do not burn the budget fighting it — two substitutes turn the same bug into an
abort with a message, which is enough for a report:

- `-D_GLIBCXX_ASSERTIONS` converts `std::vector::operator[]` and `std::map::at` violations into an abort with
the container and index in the message.
- `-fsanitize=undefined` often still links, and catches signed overflow and invalid casts.
- mmap a `PROT_NONE` page after a buffer and place the allocation against it, so a one-byte over-read faults
deterministically.

## Option 2 — extract the function and shim it

When the full build is blocked (missing dev headers, no toolchain, a submodule that will not fetch), the code
under test does not have to move:

```bash
sed -n '225,267p' src/common/cosigner/cmp_ecdsa_signing_service.cpp > ../poc/_calcR.inc
```

Include the `.inc` verbatim inside a struct with the same declaration as the header, and shim the rest with a
function-pointer table. The advantage over a re-implementation is fidelity: the bug is still in the library's
own lines, and any second agent can re-run the `sed` and diff the `.inc` against the checkout.

Two rules for a shimmed harness, both learned the hard way:

1. **Never construct an input struct by hand when the bug is about what a caller can send.** Build the input
   through the library's real parser or deserialiser, even if that means shimming more of the stack. A harness
   that assembles an impossible struct proves the struct is impossible to handle, not that a peer can send it.
2. **A shim that returns success unconditionally can hide or invent the trigger.** Stub verifiers to the value a
   real one returns on valid input, and say in the report which stubs exist.

## Option 3 — one process per case

For an API or deserialiser sweep, give the harness an `argv[1]` case selector and run it once per case from a
shell loop. One crash then does not end the sweep, and each exit code plus signal becomes a row in the evidence
table.

```bash
for c in null zero big short wrap; do ./harness $c; echo "$c exit=$?"; done
```

Keep the real output. A table of case, exit code and signal with no pasted output is not evidence.

## What to write down

Record the compiler versions, whether sanitizers were active, the exact build or extraction command, and which
parts are shimmed. If the build failed, the blocker is a useful result — name the missing dependency precisely
instead of substituting a different claim.
