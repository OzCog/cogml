;; pack-cogml.scm
;;
;; Hypergraph Pattern Encoding Package Generator for CogML
;; This script recursively collects and encodes all cognitive artifacts
;; using hypergraph pattern encoding methodology for OpenCog-style packaging.
;;
;; Usage: guile -s pack-cogml.scm [output-directory]
;;

(use-modules (ice-9 ftw)
             (ice-9 textual-ports)
             (ice-9 format)
             (srfi srfi-1))

;; Configuration constants for cognitive artifact packaging
(define *artifact-extensions* '(".scm" ".py" ".cpp" ".h" ".md" ".json"))
(define *cognitive-directories* '("scheme" "src" "opencog" "atomspace" "examples" "docs"))
(define *hypergraph-patterns* '("define" "lambda" "let" "cond" "AtomSpace" "Atom" "Node" "Link"))

;; Hypergraph pattern detection for cognitive artifacts
(define (contains-cognitive-patterns? content)
  "Check if file content contains recognized cognitive patterns"
  (any (lambda (pattern)
         (string-contains content pattern))
       *hypergraph-patterns*))

;; Extract metadata from cognitive artifacts
(define (extract-artifact-metadata filepath)
  "Extract metadata from cognitive artifact files"
  (let* ((content (if (file-exists? filepath)
                     (call-with-input-file filepath get-string-all)
                     ""))
         (size (if (file-exists? filepath) (stat:size (stat filepath)) 0))
         (cognitive-complexity (length (filter (lambda (pattern)
                                               (string-contains content pattern))
                                             *hypergraph-patterns*))))
    `((path . ,filepath)
      (size . ,size)
      (cognitive-complexity . ,cognitive-complexity)
      (has-cognitive-patterns . ,(contains-cognitive-patterns? content))
      (content-preview . ,(substring content 0 (min 200 (string-length content)))))))

;; Find all cognitive artifacts in specified directories
(define (find-artifacts base-dir)
  "Recursively find all cognitive artifact files"
  (let ((artifacts '()))
    
    ;; Simple recursive directory walker
    (define (walk-directory dir)
      (when (and (file-exists? dir) (eq? (stat:type (stat dir)) 'directory))
        (let ((entries (scandir dir)))
          (for-each (lambda (entry)
                     (unless (or (string=? entry ".") (string=? entry ".."))
                       (let ((full-path (string-append dir "/" entry)))
                         (cond
                           ((eq? (stat:type (stat full-path)) 'directory)
                            (walk-directory full-path))
                           ((eq? (stat:type (stat full-path)) 'regular)
                            (when (any (lambda (ext) (string-suffix? ext full-path)) *artifact-extensions*)
                              (set! artifacts (cons full-path artifacts))))))))
                   entries))))
    
    ;; Walk through cognitive directories if they exist
    (for-each (lambda (dir)
                (let ((full-dir (string-append base-dir "/" dir)))
                  (when (file-exists? full-dir)
                    (walk-directory full-dir))))
              *cognitive-directories*)
    
    ;; Also scan root directory for immediate files
    (when (file-exists? base-dir)
      (let ((entries (scandir base-dir)))
        (for-each (lambda (entry)
                   (unless (or (string=? entry ".") (string=? entry ".."))
                     (let ((full-path (string-append base-dir "/" entry)))
                       (when (and (eq? (stat:type (stat full-path)) 'regular)
                                 (any (lambda (ext) (string-suffix? ext full-path)) *artifact-extensions*))
                         (set! artifacts (cons full-path artifacts))))))
                 entries)))
    
    artifacts))

;; Generate hypergraph encoding for artifact collection
(define (encode-hypergraph-collection artifacts)
  "Encode artifact collection using hypergraph representation"
  (let ((total-artifacts (length artifacts))
        (cognitive-artifacts (filter (lambda (meta) 
                                     (assoc-ref meta 'has-cognitive-patterns))
                                   (map extract-artifact-metadata artifacts)))
        (total-complexity (fold + 0 (map (lambda (meta)
                                         (assoc-ref meta 'cognitive-complexity))
                                       (map extract-artifact-metadata artifacts)))))
    `((hypergraph-encoding-version . "1.0.0")
      (timestamp . ,(strftime "%Y-%m-%dT%H:%M:%SZ" (gmtime (current-time))))
      (total-artifacts . ,total-artifacts)
      (cognitive-artifacts . ,(length cognitive-artifacts))
      (cognitive-complexity-index . ,total-complexity)
      (artifacts . ,(map extract-artifact-metadata artifacts))
      (hypergraph-structure . ((nodes . ,total-artifacts)
                              (cognitive-links . ,(length cognitive-artifacts))
                              (pattern-density . ,(if (> total-artifacts 0)
                                                     (/ total-complexity total-artifacts)
                                                     0)))))))

;; Write hypergraph package to file
(define (write-hypergraph-package artifacts package-file)
  "Write hypergraph-encoded package to specified file"
  (let ((encoding (encode-hypergraph-collection artifacts)))
    (call-with-output-file package-file
      (lambda (port)
        (format port ";; CogML Hypergraph Cognitive Artifacts Package~%")
        (format port ";; Generated: ~a~%" (assoc-ref encoding 'timestamp))
        (format port ";; Total artifacts: ~a~%" (assoc-ref encoding 'total-artifacts))
        (format port ";; Cognitive complexity index: ~a~%~%" (assoc-ref encoding 'cognitive-complexity-index))
        (format port "(define cogml-hypergraph-package~%")
        (write encoding port)
        (format port ")~%~%")
        (format port ";; Package validation function~%")
        (format port "(define (validate-cogml-package)~%")
        (format port "  (and (> (assoc-ref cogml-hypergraph-package 'total-artifacts) 0)~%")
        (format port "       (string? (assoc-ref cogml-hypergraph-package 'hypergraph-encoding-version))))~%~%")
        (format port ";; Package loading complete~%")
        (format port "(display \"CogML hypergraph package loaded successfully\")~%")
        (format port "(newline)~%")))
    (format #t "Hypergraph package written to: ~a~%" package-file)))

;; Main packaging function
(define (package-hypergraph-artifacts out-dir)
  "Main function to package all hypergraph cognitive artifacts"
  (let* ((base-dir (getcwd))
         (artifacts (find-artifacts base-dir))
         (package-file (string-append out-dir "/cogml-hypergraph.scm")))
    
    ;; Ensure output directory exists
    (unless (file-exists? out-dir)
      (mkdir out-dir))
    
    ;; Generate package
    (format #t "Scanning for cognitive artifacts in: ~a~%" base-dir)
    (format #t "Found ~a potential artifacts~%" (length artifacts))
    
    (write-hypergraph-package artifacts package-file)
    
    ;; Generate summary report
    (let ((summary-file (string-append out-dir "/packaging-summary.txt")))
      (call-with-output-file summary-file
        (lambda (port)
          (format port "CogML Hypergraph Packaging Summary~%")
          (format port "Generated: ~a~%" (strftime "%Y-%m-%d %H:%M:%S" (localtime (current-time))))
          (format port "Base directory: ~a~%" base-dir)
          (format port "Output directory: ~a~%" out-dir)
          (format port "Total artifacts found: ~a~%" (length artifacts))
          (format port "Cognitive artifacts: ~a~%" 
                  (length (filter (lambda (meta) 
                                  (assoc-ref meta 'has-cognitive-patterns))
                                (map extract-artifact-metadata artifacts))))
          (format port "Package file: ~a~%" package-file)))
      (format #t "Summary written to: ~a~%" summary-file))
    
    (format #t "Hypergraph packaging completed successfully!~%")))

;; Command-line interface
(define (main args)
  (let ((out-dir (if (> (length args) 1) 
                    (cadr args) 
                    "release")))
    (format #t "CogML Hypergraph Packaging Tool~%")
    (format #t "Output directory: ~a~%" out-dir)
    (package-hypergraph-artifacts out-dir)))

;; Execute if run as script
(when (and (defined? 'command-line) (not (null? (command-line))))
  (main (command-line)))