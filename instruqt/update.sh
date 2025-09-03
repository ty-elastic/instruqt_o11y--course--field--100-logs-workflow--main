arch=linux/amd64
build=true
course=all
while getopts "a:b:c:" opt
do
   case "$opt" in
      a ) arch="$OPTARG" ;;
      b ) build="$OPTARG" ;;
      c ) course="$OPTARG" ;;
   esac
done

docker build --platform linux/amd64 -f Dockerfile.pandoc -t pandoc-inter .

# git add -u
# git commit -m "updates"
# git push origin main
# git tag -f -a $course -m $course
# git push origin $course

git tag -f -a $course -m $course
git push -f origin $course

for dir in ./courses/*/; do
  echo $dir
  if [[ -d "$dir" ]]; then
    current_course=$(basename "$dir")
    echo $current_course
    echo $course
    
    if [[ "$course" == "all" || "$course" == "$current_course" ]]; then

      if [ "$build" = "true" ]; then
        cd ..
        ./build.sh -c $current_course -a $arch -v $current_course
        cd instruqt
      fi

      cp pandoc.tex courses/$current_course/pandoc.tex
      cd courses/$current_course

      for diag in diagrams/*.mmd; do
        diag_base=$(basename "$diag")
        #mmdc -i $diag -o ./assets/$diag_base.svg
        docker run --rm -u `id -u`:`id -g` -v $PWD/diagrams:/diagrams -v $PWD/assets:/assets minlag/mermaid-cli -i /diagrams/$diag_base -o /assets/$diag_base.png
      done

      title=$(yq .title track.yml)
      echo "![](./header.png)" > input.md
      echo "" >> input.md
      echo "# $title" >> input.md
      echo "" >> input.md
      for challenge in */; do
        echo $challenge
        if [ -f "$challenge/assignment.md" ]; then
          #echo "here"

          sed -n '/---/,/---/p' "$challenge/assignment.md" > input.yaml
          ch_title=$(yq .title input.yaml)
          echo $ch_title
          rm input.yaml

          sed -e '/---/,/---/d' "$challenge/assignment.md" >> input.md
          echo "" >> input.md
          echo "___" >> input.md
          echo "" >> input.md
        fi
      done
      docker run --platform linux/amd64 --rm -v $PWD/assets:/assets -v $PWD:/data -u $(id -u):$(id -g) pandoc-inter --pdf-engine xelatex --include-in-header /data/pandoc.tex -V geometry:margin=0.25in -f markdown-implicit_figures --highlight-style=breezedark --resource-path=/assets --output=/assets/script.pdf /data/input.md
      rm -rf input.md
      docker run --platform linux/amd64 --rm -v $PWD/assets:/assets -v $PWD:/data -u $(id -u):$(id -g) pandoc-inter --pdf-engine xelatex --include-in-header /data/pandoc.tex -V geometry:margin=0.25in -f markdown-implicit_figures --highlight-style=breezedark --resource-path=/assets --output=/assets/brief.pdf /data/docs/brief.md
      docker run --platform linux/amd64 --rm -v $PWD/assets:/assets -v $PWD:/data -u $(id -u):$(id -g) pandoc-inter --pdf-engine xelatex --include-in-header /data/pandoc.tex -V geometry:margin=0.25in -f markdown-implicit_figures --highlight-style=breezedark --resource-path=/assets --output=/assets/notes.pdf /data/docs/notes.md

      instruqt track push --force
      cd ../..
      rm courses/$current_course/pandoc.tex
    fi
  fi
done





