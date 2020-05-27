# workaround for missing charset & collation support
# https://github.com/sclorg/mariadb-container/pull/125

if [ -v MYSQL_CHARSET ]; then
    log_info "Changing character set to ${MYSQL_CHARSET} ..."
    mysql $mysql_flags <<EOSQL
        ALTER DATABASE \`${MYSQL_DATABASE}\` CHARACTER SET \`${MYSQL_CHARSET}\` ;
EOSQL
fi

if [ -v MYSQL_COLLATION ]; then
    log_info "Changing collation to ${MYSQL_COLLATION} ..."
    mysql $mysql_flags <<EOSQL
        ALTER DATABASE \`${MYSQL_DATABASE}\` COLLATE \`${MYSQL_COLLATION}\` ;
EOSQL
fi
