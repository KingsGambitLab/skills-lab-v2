# Pre-built image for Skills Lab v2 Go code_exercise grading.
# Mirrors sll-python-runner / sll-node-runner for Go:
#   - go module ("skillslab") pre-initialized at /app
#   - stdlib packages warmed via a noop build so first run doesn't pay the
#     ~5-10s "go mod tidy" + module-download roundtrip
#   - Common third-party libs (gorilla/mux, uuid, testify) pre-downloaded in
#     the module cache. When the Creator emits a go.mod that pulls any of
#     these, GOPATH already has them cached.
#
# Build: docker build -t sll-go-runner:latest -f backend/docker_images/sll-go-runner.Dockerfile backend/docker_images/
#
# Per-run savings vs cold `golang:1.22-alpine`:
#   - go mod init                               ~1-2s  (now pre-baked)
#   - go mod tidy + stdlib resolution           ~3-5s  (now warm)
#   - first-ever `go test` stdlib compile cache ~5-10s (now warm)
# Total: ~10-15s off every code_exercise invariant check.

FROM golang:1.22-alpine

ENV CGO_ENABLED=0 \
    GOFLAGS="-mod=mod" \
    GOCACHE=/runner/.cache/go-build \
    GOMODCACHE=/runner/.cache/go-mod

WORKDIR /runner

# Warm the stdlib build cache with a minimal noop program.
RUN mkdir -p /runner/warmup && \
    cat > /runner/warmup/main.go <<'EOF'
package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"sync"
	"time"
)

var _ = context.Background
var _ = json.Marshal
var _ = errors.New
var _ = fmt.Sprintf
var _ = io.Copy
var _ = http.Get
var _ = url.Parse
var _ = os.Getenv
var _ = regexp.MustCompile
var _ = sort.Strings
var _ = strconv.Atoi
var _ = strings.Contains
var _ = sync.Mutex{}
var _ = time.Now
func main() {}
EOF

# Pre-download + pre-compile with common 3rd-party libs so the module cache
# has them ready. When Creator-emitted tests pull these, no network fetch.
RUN cd /runner/warmup && \
    go mod init warmup && \
    go get \
        github.com/google/uuid@v1.6.0 \
        github.com/stretchr/testify@v1.10.0 \
        github.com/gorilla/mux@v1.8.1 && \
    go build -o /dev/null ./... && \
    go test -count=1 ./... 2>&1 | tail -1 && \
    echo "warmup ok"

# App mount point — the backend writes solution.go + solution_test.go here.
# Pre-baked go.mod so `go mod init` is unnecessary at test time.
WORKDIR /app
RUN cat > /app/go.mod <<'EOF'
module skillslab

go 1.22
EOF

# Confirm the tooling works at build time.
RUN go version && echo "sll-go-runner ready"
