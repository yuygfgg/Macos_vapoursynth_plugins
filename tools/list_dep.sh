#!/bin/bash

# 定义一个数组来存储所有依赖项
dependencies=()

# 遍历所有 .dylib 文件
for file in *.dylib; do
  # 使用 otool 获取依赖项，并提取相关行
  deps=$(otool -L "$file" | awk 'NR>1 {print $1}')
  
  # 将每个依赖项添加到数组中，忽略自身和 @rpath 开头的项
  for dep in $deps; do
    if [[ "$dep" != "$file" && "$dep" != @rpath* ]]; then
      dependencies+=("$dep ($file)")
    fi
  done
done

# 去重并排序
sorted_unique_dependencies=$(printf "%s\n" "${dependencies[@]}" | sort -u)

# 输出结果
echo "所有依赖项："
printf "%s\n" "$sorted_unique_dependencies"
